from __future__ import annotations

import re
from html.parser import HTMLParser

import httpx

_URL_RE = re.compile(r"https?://[^\s<>\"']+")


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self._skip = True

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"}:
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            t = data.strip()
            if t:
                self._chunks.append(t)

    def text(self) -> str:
        return "\n".join(self._chunks)


async def enrich_supplied_sources(raw: str, max_chars_per_url: int = 3500) -> str:
    """Keep user excerpts; fetch readable text for any URLs (Limited mode study)."""
    raw = (raw or "").strip()
    if not raw:
        return "(none provided)"
    urls = _URL_RE.findall(raw)
    parts = [f"USER-PROVIDED TEXT/LINKS:\n{raw}"]
    if not urls:
        return "\n\n".join(parts)
    parts.append("FETCHED PAGE EXTRACTS (for argument grounding):")
    async with httpx.AsyncClient(
        timeout=20.0,
        follow_redirects=True,
        headers={"User-Agent": "HistoricalDialecticsStudio/0.2"},
    ) as client:
        for url in urls[:5]:
            try:
                r = await client.get(url)
                r.raise_for_status()
                ctype = r.headers.get("content-type", "")
                body = r.text
                if "html" in ctype.lower() or body.lstrip().startswith("<"):
                    parser = _TextExtractor()
                    parser.feed(body)
                    text = parser.text()
                else:
                    text = body
                text = re.sub(r"\n{3,}", "\n\n", text)[:max_chars_per_url]
                parts.append(f"--- FROM {url} ---\n{text}")
            except Exception as exc:  # noqa: BLE001
                parts.append(f"--- FROM {url} ---\n(Fetch failed: {exc})")
    return "\n\n".join(parts)
