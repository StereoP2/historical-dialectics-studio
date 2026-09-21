from __future__ import annotations

from pathlib import Path

DOSSIER_DIR = Path(__file__).resolve().parent.parent / "character_dossiers"
_CACHE: dict[str, str] = {}


def load_dossier(persona_id: str) -> str:
    if persona_id in _CACHE:
        return _CACHE[persona_id]
    path = DOSSIER_DIR / f"{persona_id}.txt"
    if not path.exists():
        text = (
            f"(No dossier file for {persona_id}.) Stay strictly in-character; "
            "never adopt a generic presidential/CEO tone."
        )
    else:
        text = path.read_text(encoding="utf-8").strip()
    _CACHE[persona_id] = text
    return text


def preload_all_dossiers() -> dict[str, str]:
    """Study every character dossier up front (including inactive seats)."""
    out: dict[str, str] = {}
    if DOSSIER_DIR.exists():
        for path in sorted(DOSSIER_DIR.glob("*.txt")):
            out[path.stem] = load_dossier(path.stem)
    return out
