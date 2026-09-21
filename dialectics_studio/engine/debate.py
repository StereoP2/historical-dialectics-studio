from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Awaitable, Callable

from .demo_script import DEMO_ROUNDS
from .llm import api_configured, complete, load_prompt
from .personas import ARCHETYPE_RULES, Persona


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
    ) -> None:
        use_live = (not force_demo) and api_configured(self.api_key)
        if not use_live:
            await _emit(
                on_event,
                DebateEvent(
                    "status",
                    "system",
                    "System",
                    "Demo mode (no API key) — playing sample Marx vs Descartes transcript.",
                ),
            )
            await self._run_demo(on_event)
            return

        await _emit(
            on_event,
            DebateEvent("status", "system", "System", "Live multi-agent debate started."),
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
                )
                user = f"Round {r + 1}. Deliver your next argument on: {topic}"
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
                    topic=topic, speaker=persona.name, turn_text=text
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
