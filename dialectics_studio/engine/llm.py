from __future__ import annotations

import os
from pathlib import Path

import httpx

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / name
    if not path.exists():
        alt = Path(__file__).resolve().parents[2] / "prompts" / name
        path = alt
    return path.read_text(encoding="utf-8")


def api_configured(api_key: str | None = None) -> bool:
    return bool(
        api_key
        or os.environ.get("OPENAI_API_KEY")
        or os.environ.get("HDS_API_KEY")
    )


async def complete(system: str, user: str, api_key: str | None = None) -> str:
    key = api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("HDS_API_KEY")
    if not key:
        raise RuntimeError("No API key configured")
    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("HDS_MODEL", "gpt-4o-mini")
    async with httpx.AsyncClient(timeout=90.0) as client:
        r = await client.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": model,
                "temperature": 0.7,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"].strip()
