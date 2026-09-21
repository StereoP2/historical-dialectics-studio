from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dialectics_studio.engine.discussion import DiscussionSession
from dialectics_studio.engine.debate import DebateEngine, DebateEvent
from dialectics_studio.engine.personas import PERSONAS, TOPICS, get_persona

STATIC = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Historical Dialectics Studio")
sessions: dict[str, DiscussionSession] = {}



def _event_dict(ev: DebateEvent) -> dict[str, Any]:
    return {
        "kind": ev.kind,
        "speaker_id": ev.speaker_id,
        "speaker_name": ev.speaker_name,
        "text": ev.text,
    }


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/api/roster")
async def roster() -> dict[str, Any]:
    return {
        "personas": [
            {
                "id": p.id,
                "name": p.name,
                "years": p.years,
                "archetype": p.archetype,
                "color": p.color,
                "blurb": p.blurb,
            }
            for p in PERSONAS
        ],
        "topics": TOPICS,
    }


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    session_id: str | None = None
    try:
        while True:
            msg = await websocket.receive_json()
            op = msg.get("op")
            if op == "start":
                topic = (msg.get("topic") or "").strip()
                ids = msg.get("persona_ids") or []
                if not topic or not ids:
                    await websocket.send_json(
                        {"kind": "error", "speaker_id": "system",
                         "speaker_name": "System", "text": "Pick a topic and 1–3 thinkers."}
                    )
                    continue
                try:
                    debaters = [get_persona(pid) for pid in ids[:3]]
                except KeyError as exc:
                    await websocket.send_json(
                        {"kind": "error", "speaker_id": "system",
                         "speaker_name": "System", "text": f"Unknown persona: {exc}"}
                    )
                    continue

                mode = (msg.get("mode") or "discussion").lower()
                api_key = (msg.get("api_key") or "") or None
                source_mode = msg.get("source_mode") or "Free"
                supplied = msg.get("supplied_sources") or ""

                if mode == "fishbowl":
                    session_id = str(uuid.uuid4())
                    await websocket.send_json(
                        {"kind": "status", "speaker_id": "system",
                         "speaker_name": "System",
                         "text": "Fishbowl started (watch-only)."}
                    )
                    engine = DebateEngine(api_key=api_key)

                    async def on_event(ev: DebateEvent) -> None:
                        await websocket.send_json(_event_dict(ev))

                    await engine.run(
                        topic,
                        debaters,
                        int(msg.get("rounds") or 2),
                        on_event,
                        source_mode=source_mode,
                        supplied_sources=supplied,
                    )
                    continue

                # discussion (join) mode
                sess = DiscussionSession(
                    topic=topic,
                    debaters=debaters,
                    source_mode=source_mode,
                    supplied_sources=supplied,
                    api_key=api_key,
                )
                session_id = str(uuid.uuid4())
                sessions[session_id] = sess
                await websocket.send_json({"kind": "session", "session_id": session_id})
                async for ev in sess.start():
                    await websocket.send_json(_event_dict(ev))

            elif op == "speak":
                sid = msg.get("session_id") or session_id
                text = msg.get("text") or ""
                sess = sessions.get(sid) if sid else None
                if not sess:
                    await websocket.send_json(
                        {"kind": "error", "speaker_id": "system",
                         "speaker_name": "System",
                         "text": "No active discussion — click Start discussion first."}
                    )
                    continue
                async for ev in sess.user_turn(text):
                    await websocket.send_json(_event_dict(ev))
            else:
                await websocket.send_json(
                    {"kind": "error", "speaker_id": "system",
                     "speaker_name": "System", "text": f"Unknown op: {op}"}
                )
    except WebSocketDisconnect:
        if session_id and session_id in sessions:
            sessions.pop(session_id, None)


def main() -> None:
    import uvicorn

    print("Historical Dialectics Studio (web)")
    print("Open http://127.0.0.1:7860 in your browser")
    uvicorn.run(
        "dialectics_studio.web.app:app",
        host="127.0.0.1",
        port=7860,
        reload=False,
    )


if STATIC.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")
