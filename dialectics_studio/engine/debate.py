from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from typing import Awaitable, Callable

from .demo_script import DEMO_ROUNDS
from .dossiers import load_dossier, preload_all_dossiers
from .llm import api_configured, complete, load_prompt
from .personas import ARCHETYPE_RULES, Persona
from .sources import enrich_supplied_sources

FREE_RULES = (
    "FREE SOURCE MODE: Cite historically plausible sources in YOUR tradition "
    "(your works, contemporaries, public records). Prefer real titles/years/passages. "
    "Do not invent fake URLs. Still stay on the USER TOPIC."
)

LIMITED_RULES = (
    "LIMITED SOURCE MODE — ABSOLUTE: You may ONLY use SUPPLIED MATERIALS below "
    "(user text + fetched extracts). Forbidden: outside books, famous quotes not in materials, "
    "stats, or URLs not listed. Every [Source: …] must point to supplied material. "
    "If materials lack what you need, admit the gap in character and argue from what IS there. "
    "Violating this gets INVALIDATED."
)

_INVALIDATE_RE = re.compile(r"INVALIDATE:\s*(YES|NO)", re.IGNORECASE)


@dataclass
class DebateEvent:
    kind: str  # debater | factcheck | invalidate | status | error
    speaker_id: str
    speaker_name: str
    text: str


ProgressCb = Callable[[DebateEvent], Awaitable[None] | None]


class DebateEngine:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key
        # Study all dossiers even for inactive seats
        self._dossier_index = preload_all_dossiers()

    async def run(
        self,
        topic: str,
        debaters: list[Persona],
        rounds: int,
        on_event: ProgressCb,
        force_demo: bool = False,
        source_mode: str = "Free",
        supplied_sources: str = "",
    ) -> None:
        mode = "Limited" if source_mode.lower().startswith("limit") else "Free"
        raw_materials = (supplied_sources or "").strip()
        mode_rules = LIMITED_RULES if mode == "Limited" else FREE_RULES

        use_live = (not force_demo) and api_configured(self.api_key)
        if not use_live:
            await _emit(
                on_event,
                DebateEvent(
                    "status",
                    "system",
                    "System",
                    "Demo mode (no API key). Add an API key for live Free/Limited debates "
                    f"on your topic. Dossiers loaded: {len(self._dossier_index)} characters studied.",
                ),
            )
            await self._run_demo(on_event)
            return

        if mode == "Limited" and not raw_materials:
            await _emit(
                on_event,
                DebateEvent(
                    "error",
                    "system",
                    "System",
                    "Limited mode needs at least one link or excerpt.",
                ),
            )
            return

        await _emit(
            on_event,
            DebateEvent(
                "status",
                "system",
                "System",
                f"Studied {len(self._dossier_index)} character dossiers. "
                f"Reading supplied sources ({mode})…",
            ),
        )
        materials = await enrich_supplied_sources(raw_materials) if raw_materials else "(none provided)"
        if mode == "Free" and materials == "(none provided)":
            materials = "(none — Free mode: use your own historically grounded sources)"

        await _emit(
            on_event,
            DebateEvent(
                "status",
                "system",
                "System",
                f"Live debate · TOPIC LOCK: «{topic}» · source mode: {mode}",
            ),
        )

        history: list[tuple[str, str]] = []
        debater_prompt = load_prompt("debater_system.txt")
        fact_prompt = load_prompt("historiographer_system.txt")
        pending_correction: dict[str, str] = {}

        for r in range(rounds):
            for persona in debaters:
                prior = "\n".join(f"{n}: {t}" for n, t in history[-6:]) or "(opening)"
                dossier = load_dossier(persona.id)
                system = debater_prompt.format(
                    name=persona.name,
                    years=persona.years,
                    archetype=persona.archetype,
                    archetype_rules=ARCHETYPE_RULES[persona.archetype],
                    topic=topic,
                    prior_context=prior,
                    source_mode=mode,
                    source_mode_rules=mode_rules,
                    supplied_sources=materials,
                    character_dossier=dossier,
                )
                user = (
                    f"Round {r + 1}. USER TOPIC (do not change subject): {topic}\n"
                    f"Source mode: {mode}.\n"
                    f"Argue from YOUR individual POV as {persona.name} only.\n"
                )
                if persona.id in pending_correction:
                    user += (
                        "\nHISTORIOGRAPHER INVALIDATED your last turn:\n"
                        f"{pending_correction.pop(persona.id)}\n"
                        "Reply with a corrected argument on the SAME topic.\n"
                    )
                try:
                    text = await complete(system, user, self.api_key)
                except Exception as exc:  # noqa: BLE001
                    await _emit(
                        on_event,
                        DebateEvent("error", "system", "System", f"LLM error: {exc}"),
                    )
                    return

                await _emit(
                    on_event,
                    DebateEvent("debater", persona.id, persona.name, text),
                )

                fsys = fact_prompt.format(
                    topic=topic,
                    speaker=persona.name,
                    turn_text=text,
                    source_mode=mode,
                    supplied_sources=materials,
                )
                try:
                    ftext = await complete(
                        fsys, "Referee this turn now.", self.api_key
                    )
                except Exception as exc:  # noqa: BLE001
                    ftext = f"INVALIDATE: NO\nREASON: Fact-check unavailable ({exc})"

                invalidated = _is_invalidated(ftext)
                await _emit(
                    on_event,
                    DebateEvent(
                        "factcheck",
                        "historiographer",
                        "The Historiographer",
                        ftext,
                    ),
                )
                if invalidated:
                    await _emit(
                        on_event,
                        DebateEvent(
                            "invalidate",
                            "historiographer",
                            "The Historiographer",
                            f"INVALIDATED {persona.name}'s turn — argument void for the record. "
                            "They must correct next time they speak.",
                        ),
                    )
                    pending_correction[persona.id] = ftext
                    # Do not add invalidated text as settled history
                    history.append(
                        (
                            persona.name,
                            f"[INVALIDATED TURN — void]\n{text}",
                        )
                    )
                else:
                    history.append((persona.name, text))

        await _emit(
            on_event,
            DebateEvent("status", "system", "System", "Debate complete."),
        )

    async def _run_demo(self, on_event: ProgressCb) -> None:
        names = {
            "marx": "Karl Marx",
            "descartes": "René Descartes",
            "historiographer": "The Historiographer",
        }
        for step in DEMO_ROUNDS:
            sid = step["speaker"]
            kind = "factcheck" if sid == "historiographer" else "debater"
            await asyncio.sleep(0.35)
            await _emit(
                on_event,
                DebateEvent(kind, sid, names[sid], step["text"]),
            )
        await _emit(
            on_event,
            DebateEvent("status", "system", "System", "Demo debate complete."),
        )


def _is_invalidated(fact_text: str) -> bool:
    m = _INVALIDATE_RE.search(fact_text or "")
    return bool(m and m.group(1).upper() == "YES")


async def _emit(cb: ProgressCb, event: DebateEvent) -> None:
    result = cb(event)
    if asyncio.iscoroutine(result):
        await result
