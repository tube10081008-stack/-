#!/usr/bin/env python3
"""필담 서버 — 런타임 생성 채팅.

실행:
    GEMINI_API_KEY=... python3 server/app.py            # http://127.0.0.1:8000
"""
from __future__ import annotations

import pathlib
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

import engine

HERE = pathlib.Path(__file__).resolve().parent
ROOMS = {
    "shakespeare.sonnet18": {"writer": "shakespeare", "title": "소네트 18",
                             "hook": "연인을 찬미하다 결국 자기 시를 자랑하는 열네 행"},
    "shakespeare.hamlet": {"writer": "shakespeare", "title": "햄릿 · 3막 1장",
                           "hook": "가장 유명한 대사가 실은 아무것도 결정하지 못한다"},
    "austen.pp": {"writer": "austen", "title": "오만과 편견 · 다아시의 편지",
                  "hook": "당신의 감정이 아니라 정의감에 요구한다"},
}

app = FastAPI(title="pildam")
SESSIONS: dict[str, engine.Session] = {}
EMBEDDINGS: dict[str, list[float]] = {}


@app.on_event("startup")
def _warm() -> None:
    EMBEDDINGS.update(engine.span_embeddings())
    print(f"[pildam] {len(EMBEDDINGS)} span 임베딩 준비 완료")


class Open(BaseModel):
    room: str
    tau: int = 2


class Say(BaseModel):
    session_id: str
    text: str


@app.get("/")
def index() -> FileResponse:
    return FileResponse(HERE / "client.html")


@app.get("/api/rooms")
def rooms() -> dict:
    return {"rooms": [{"id": rid, **meta,
                       "writer_name": engine.CARDS[meta["writer"]]["name"],
                       "died": engine.CARDS[meta["writer"]]["died"]}
                      for rid, meta in ROOMS.items()]}


@app.post("/api/open")
def open_room(body: Open) -> dict:
    meta = ROOMS.get(body.room)
    if not meta:
        raise HTTPException(404, "없는 방")
    sid = uuid.uuid4().hex[:12]
    SESSIONS[sid] = engine.Session(room=body.room, writer=meta["writer"], tau=body.tau)
    return {"session_id": sid, "writer": engine.CARDS[meta["writer"]]["name"],
            "died": engine.CARDS[meta["writer"]]["died"], "title": meta["title"], "tau": body.tau}


@app.post("/api/turn")
def take_turn(body: Say) -> dict:
    session = SESSIONS.get(body.session_id)
    if not session:
        raise HTTPException(404, "세션 없음")
    try:
        return engine.turn(session, body.text, EMBEDDINGS)
    except Exception as exc:                                     # noqa: BLE001
        raise HTTPException(502, f"생성 실패: {exc}") from exc


@app.post("/api/tau")
def bump_tau(body: Say) -> dict:
    session = SESSIONS.get(body.session_id)
    if not session:
        raise HTTPException(404, "세션 없음")
    session.tau += int(body.text or 20)
    return {"tau": session.tau}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
