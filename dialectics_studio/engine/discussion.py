from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import AsyncIterator

from .debate import (
    FREE_RULES,
    LIMITED_RULES,
    DebateEvent,
    _is_invalidated,
)
from .demo_script import DEMO_ROUNDS
from .dossiers import load_dossier, preload_all_dossiers
from .llm import api_configured, complete, load_prompt
from .personas import ARCHETYPE_RULES, Persona
from .sources import enrich_supplied_sources


@dataclass
class DiscussionSession:
    """Interactive Arena: user argues with thinkers (not fishbowl-only)."""

    topic: str
    debaters: list[Persona]
    source_mode: str = "Free"
    supplied_sources: str = ""
    api_key: str | None = None
    history: list[tuple[str, str]] = field(default_factory=list)
    materials: str = ""
    mode: str = "Free"
    mode_rules: str = FREE_RULES
    pending_correction: dict[str, str] = field(default_factory=dict)
    ready: bool = False
    _dossier_index: dict = field(default_factory=dict)

    async def start(self) -> AsyncIterator[DebateEvent]:
        self._dossier_index = preload_all_dossiers()
        self.mode = "Limited" if self.source_mode.lower().startswith("limit") else "Free"
        self.mode_rules = LIMITED_RULES if self.mode == "Limited" else FREE_RULES
        raw = (self.supplied_sources or "").strip()

        if self.mode == "Limited" and not raw and api_configured(self.api_key):
            yield DebateEvent(
                "error",
                "system",
                "System",
                "Limited mode needs at least one link or excerpt.",
            )
            return

        yield DebateEvent(
            "status",
            "system",
            "System",
            f"Discussion mode · you are in the Arena with "
            f"{', '.join(p.name for p in self.debaters)}. "
            f"TOPIC LOCK: «{self.topic}» · {self.mode} sources · "
            f"{len(self._dossier_index)} dossiers studied.",
        )

        if raw and api_configured(self.api_key):
            yield DebateEvent(
                "status", "system", "System", "Reading supplied sources…"
            )
            self.materials = await enrich_supplied_sources(raw)
        elif raw:
            self.materials = raw
        elif self.mode == "Free":
            self.materials = (
                "(none — Free mode: use your own historically grounded sources)"
            )
        else:
            self.materials = "(none provided)"

        self.ready = True
        yield DebateEvent(
            "status",
            "system",
            "System",
            "Type your argument below. Thinkers will reply to you, not just each other.",
        )

    async def user_turn(self, user_text: str) -> AsyncIterator[DebateEvent]:
        text = (user_text or "").strip()
        if not text:
            yield DebateEvent("error", "system", "System", "Say something first.")
            return
        if not self.ready:
            yield DebateEvent(
                "error", "system", "System", "Start a discussion before speaking."
            )
            return

        yield DebateEvent("debater", "you", "You", text)

        if not api_configured(self.api_key):
            async for ev in self._demo_user_turn(text):
                yield ev
            return

        fact_prompt = load_prompt("historiographer_system.txt")
        fsys = fact_prompt.format(
            topic=self.topic,
            speaker="You (participant)",
            turn_text=text,
            source_mode=self.mode,
            supplied_sources=self.materials,
        )
        try:
            ftext = await complete(fsys, "Referee this turn now.", self.api_key)
        except Exception as exc:  # noqa: BLE001
            ftext = f"INVALIDATE: NO\nREASON: Fact-check unavailable ({exc})"

        yield DebateEvent(
            "factcheck", "historiographer", "The Historiographer", ftext
        )
        if _is_invalidated(ftext):
            yield DebateEvent(
                "invalidate",
                "historiographer",
                "The Historiographer",
                "INVALIDATED your turn — refine it; thinkers will still respond, but note the flags.",
            )
            self.history.append(("You", f"[FLAGGED]\n{text}"))
        else:
            self.history.append(("You", text))

        debater_prompt = load_prompt("debater_system.txt")
        for persona in self.debaters:
            prior = "\n".join(f"{n}: {t}" for n, t in self.history[-8:]) or "(opening)"
            dossier = load_dossier(persona.id)
            system = debater_prompt.format(
                name=persona.name,
                years=persona.years,
                archetype=persona.archetype,
                archetype_rules=ARCHETYPE_RULES[persona.archetype],
                topic=self.topic,
                prior_context=prior,
                source_mode=self.mode,
                source_mode_rules=self.mode_rules,
                supplied_sources=self.materials,
                character_dossier=dossier,
            )
            user = (
                f"DISCUSSION MODE: The living participant (You) just argued.\n"
                f"USER TOPIC (do not change subject): {self.topic}\n"
                f"Source mode: {self.mode}.\n"
                f"Respond directly to You — challenge, question, or grant points "
                f"from YOUR individual POV as {persona.name} only. "
                f"Do not ignore their last message.\n"
            )
            if persona.id in self.pending_correction:
                user += (
                    "\nHISTORIOGRAPHER INVALIDATED your last turn:\n"
                    f"{self.pending_correction.pop(persona.id)}\n"
                    "Correct on the SAME topic while answering You.\n"
                )
            try:
                reply = await complete(system, user, self.api_key)
            except Exception as exc:  # noqa: BLE001
                yield DebateEvent("error", "system", "System", f"LLM error: {exc}")
                return

            yield DebateEvent("debater", persona.id, persona.name, reply)

            fsys2 = fact_prompt.format(
                topic=self.topic,
                speaker=persona.name,
                turn_text=reply,
                source_mode=self.mode,
                supplied_sources=self.materials,
            )
            try:
                ftext2 = await complete(
                    fsys2, "Referee this turn now.", self.api_key
                )
            except Exception as exc:  # noqa: BLE001
                ftext2 = f"INVALIDATE: NO\nREASON: Fact-check unavailable ({exc})"

            yield DebateEvent(
                "factcheck", "historiographer", "The Historiographer", ftext2
            )
            if _is_invalidated(ftext2):
                yield DebateEvent(
                    "invalidate",
                    "historiographer",
                    "The Historiographer",
                    f"INVALIDATED {persona.name}'s turn — they must correct next speak.",
                )
                self.pending_correction[persona.id] = ftext2
                self.history.append(
                    (persona.name, f"[INVALIDATED TURN — void]\n{reply}")
                )
            else:
                self.history.append((persona.name, reply))

    async def _demo_user_turn(self, user_text: str) -> AsyncIterator[DebateEvent]:
        self.history.append(("You", user_text))
        yield DebateEvent(
            "factcheck",
            "historiographer",
            "The Historiographer",
            "INVALIDATE: NO\nREASON: Demo referee — add an API key for live checks.\n"
            "FLAGS:\n- Low | Demo | Live discussion needs a key | —\n"
            "VOICE_NOTE: n/a\nTOPIC_NOTE: assumed on-topic\nSOURCE_NOTE: demo",
        )
        # Reuse a couple of demo lines adapted as replies
        snippets = [s for s in DEMO_ROUNDS if s["speaker"] != "historiographer"]
        for i, persona in enumerate(self.debaters):
            base = snippets[i % len(snippets)]["text"]
            reply = (
                f"(Demo reply as {persona.name} — add an API key for live voice.)\n"
                f"You claimed: «{user_text[:120]}{'…' if len(user_text) > 120 else ''}». "
                f"I answer from my station: {base[:280]}"
            )
            await asyncio.sleep(0.25)
            yield DebateEvent("debater", persona.id, persona.name, reply)
            yield DebateEvent(
                "factcheck",
                "historiographer",
                "The Historiographer",
                "INVALIDATE: NO\nREASON: Demo turn.\nFLAGS:\n- Info | Demo | — | —\n"
                "VOICE_NOTE: canned\nTOPIC_NOTE: demo\nSOURCE_NOTE: demo",
            )
            self.history.append((persona.name, reply))
