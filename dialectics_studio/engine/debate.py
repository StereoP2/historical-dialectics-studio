from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Awaitable, Callable

from .demo_script import DEMO_ROUNDS
from .llm import api_configured, complete, load_prompt
from .personas import ARCHETYPE_RULES, Persona

FREE_RULES = (
    "FREE SOURCE MODE: You may draw on any historically plausible sources in your "
    "tradition — your own works, contemporaries, public records, well-known data. "
    "Prefer specific titles, years, and passages. Do not invent fake URLs; if unsure, "
    "cite a real work or say [Source: inferred from X tradition, unverified]."
)

LIMITED_RULES = (
    "LIMITED SOURCE MODE: You may ONLY cite and argue from the SUPPLIED MATERIALS below "
    "(links and/or excerpts), plus your persona's interpretive lens. "
    "Do not introduce outside books, stats, or URLs. Quote or paraphrase the supplied "
    "text with [Source: supplied excerpt/link]. If materials are thin, say so in character "
    "and press opponents on what the materials do and do not show."
)


@dataclass
class DebateEvent:
    kind: str  # debater | factcheck | status | error
    speaker_id: str
    speaker_name: str
    text: str


ProgressCb = Callable[[DebateEvent], Awaitable[None] | None]


class DebateEngine:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key

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
        materials = (supplied_sources or "").strip() or "(none provided)"
        mode_rules = LIMITED_RULES if mode == "Limited" else FREE_RULES

        use_live = (not force_demo) and api_configured(self.api_key)
        if not use_live:
            await _emit(
                on_event,
                DebateEvent(
                    "status",
                    "system",
                    "System",
                    "Demo mode (no API key) — playing sample Marx vs Descartes transcript. "
                    "Add an API key for live Free/Limited source debates on your custom topic.",
                ),
            )
            await self._run_demo(on_event)
            return

        if mode == "Limited" and materials == "(none provided)":
            await _emit(
                on_event,
                DebateEvent(
                    "error",
                    "system",
                    "System",
                    "Limited mode needs at least one link or excerpt in the sources box.",
                ),
            )
            return

        await _emit(
            on_event,
            DebateEvent(
                "status",
                "system",
                "System",
                f"Live debate · topic: {topic} · source mode: {mode}",
            ),
        )
        history: list[tuple[str, str]] = []
        debater_prompt = load_prompt("debater_system.txt")
        fact_prompt = load_prompt("historiographer_system.txt")

        for r in range(rounds):
            for persona in debaters:
                prior = "\n".join(f"{n}: {t}" for n, t in history[-6:]) or "(opening)"
                system = debater_prompt.format(
                    name=persona.name,
                    years=persona.years,
                    archetype=persona.archetype,
                    archetype_rules=ARCHETYPE_RULES[persona.archetype],
                    death_year=persona.death_year,
                    topic=topic,
                    prior_context=prior,
                    source_mode=mode,
                    source_mode_rules=mode_rules,
                    supplied_sources=materials,
                )
                user = (
                    f"Round {r + 1}. Argue freshly on this topic (not a canned speech): {topic}\n"
                    f"Source mode: {mode}. Use sources as required by your system rules."
                )
                try:
                    text = await complete(system, user, self.api_key)
                except Exception as exc:  # noqa: BLE001
                    await _emit(
                        on_event,
                        DebateEvent("error", "system", "System", f"LLM error: {exc}"),
                    )
                    return
                history.append((persona.name, text))
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
                        fsys, "Produce the fact-check now.", self.api_key
                    )
                except Exception as exc:  # noqa: BLE001
                    ftext = f"(Fact-check unavailable: {exc})"
                await _emit(
                    on_event,
                    DebateEvent(
                        "factcheck",
                        "historiographer",
                        "The Historiographer",
                        ftext,
                    ),
                )

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


async def _emit(cb: ProgressCb, event: DebateEvent) -> None:
    result = cb(event)
    if asyncio.iscoroutine(result):
        await result
