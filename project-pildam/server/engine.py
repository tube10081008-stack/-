#!/usr/bin/env python3
"""필담 대화 엔진 — 런타임 생성판.

하드코딩된 의도 테이블도, 미리 적어 둔 응답 뱅크도 없다.
손으로 쓰는 것은 셋뿐이다: 문우 카드, 코퍼스, 계약.

한 턴의 흐름 (04장 파이프라인):
  ① 읽기   — 모델이 독자의 발화를 읽고 상태 신호만 보고한다 (분류 enum 아님)
  ② 정책   — 코드가 (δ, π)를 결정한다. 이건 모델에게 맡기지 않는다. 논지이기 때문이다
  ③ 검색   — 임베딩 유사도 + 정책 보정. 키워드 표 없음
  ④ MIP    — 선행 span을 자르지 않고 확장
  ⑤ 쓰기   — 모델이 프레임만 쓴다. span_id는 고르되 인용문 텍스트는 만들지 않는다
  ⑥ 검증   — 코드가 계약을 집행한다. 위반이면 재생성, 두 번 실패하면 원문 단독
"""
from __future__ import annotations

import json
import math
import os
import pathlib
import sys
from dataclasses import dataclass, field

import requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from validate_response import validate  # noqa: E402

API = "https://generativelanguage.googleapis.com/v1beta/models/{m}:{op}"
READ_MODEL = os.environ.get("PILDAM_READ_MODEL", "gemini-2.5-flash")
WRITE_MODEL = os.environ.get("PILDAM_WRITE_MODEL", "gemini-3.1-pro-preview")
EMBED_MODEL = "gemini-embedding-001"
APPEAL_TAU = 10
VQR_FLOOR_APPEAL = 0.75

CORPUS = json.loads((ROOT / "corpus/pildam-v2.json").read_text(encoding="utf-8"))["spans"]
CARDS = json.loads((ROOT / "server/writers.json").read_text(encoding="utf-8"))


def _key() -> str:
    k = os.environ.get("GEMINI_API_KEY")
    if not k:
        raise RuntimeError("GEMINI_API_KEY 환경변수가 필요합니다.")
    return k


def _post(model: str, op: str, payload: dict, timeout: int = 120) -> dict:
    r = requests.post(API.format(m=model, op=op), params={"key": _key()},
                      json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()


def _generate(model: str, system: str, user: str, schema: dict, temp: float = 0.9) -> dict:
    data = _post(model, "generateContent", {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {"responseMimeType": "application/json", "responseSchema": schema,
                             "temperature": temp, "maxOutputTokens": 4096},
    })
    cand = data["candidates"][0]
    text = "".join(p.get("text", "") for p in (cand.get("content", {}).get("parts") or []))
    if not text.strip():
        raise RuntimeError(f"빈 응답 (finishReason={cand.get('finishReason')})")
    return json.loads(text)


# ────────────────────────────────────────────────── 임베딩 검색

_EMB_CACHE = ROOT / "corpus" / "embeddings.json"


def _embed(text: str) -> list[float]:
    d = _post(EMBED_MODEL, "embedContent", {
        "model": f"models/{EMBED_MODEL}",
        "content": {"parts": [{"text": text[:4000]}]},
        "outputDimensionality": 768,
    })
    return d["embedding"]["values"]


def span_embeddings() -> dict[str, list[float]]:
    if _EMB_CACHE.exists():
        cached = json.loads(_EMB_CACHE.read_text(encoding="utf-8"))
        if set(cached) == set(CORPUS):
            return cached
    out = {}
    for sid, s in CORPUS.items():
        blob = " / ".join([s["work_title"], s["locus"], ", ".join(s.get("income_tags", [])),
                           s.get("wildness_note", ""), s["text_ko"]])
        out[sid] = _embed(blob)
    _EMB_CACHE.write_text(json.dumps(out), encoding="utf-8")
    return out


def _cos(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


# ────────────────────────────────────────────────── 상태

@dataclass
class Session:
    room: str
    writer: str
    tau: int = 2
    turns: int = 0
    shown: list[str] = field(default_factory=list)
    used: list[str] = field(default_factory=list)
    highlights: list[str] = field(default_factory=list)
    stance: str | None = None
    stance_target: str | None = None
    history: list[dict] = field(default_factory=list)


# ────────────────────────────────────────────────── ① 읽기

READ_SCHEMA = {"type": "OBJECT", "properties": {
    "asserted_stance": {"type": "STRING", "description": "독자가 내린 판정. 없으면 빈 문자열"},
    "stance_target": {"type": "STRING", "description": "그 판정이 향한 인물. 없으면 빈 문자열"},
    "wants_summary": {"type": "BOOLEAN"},
    "is_small_talk": {"type": "BOOLEAN", "description": "인사·잡담·서비스 자체에 대한 질문 등 읽기와 무관한 발화"},
    "asks_what_you_are": {"type": "BOOLEAN", "description": "정체·AI 여부를 물음"},
    "engagement": {"type": "STRING", "description": "probing | agreeing | resisting | drifting 중 하나"},
    "note": {"type": "STRING", "description": "이 발화에서 읽어 낸 것 한 줄"},
}, "required": ["asserted_stance", "stance_target", "wants_summary", "is_small_talk",
                "asks_what_you_are", "engagement", "note"]}

READ_SYSTEM = """너는 독서 대화 시스템의 관찰자다. 독자의 발화를 읽고 상태 신호만 보고한다.
너는 답하지 않는다. 분류하지 말고 관찰하라 — 정해진 범주에 억지로 끼워 맞추지 마라.
독자가 확신에 찬 판정을 내렸는지, 동의만 반복하는지, 저항하는지, 딴 데로 새는지를 본다."""


def read_reader(session: Session, text: str) -> dict:
    recent = session.history[-6:]
    user = json.dumps({
        "독자_발화": text,
        "직전_대화": recent,
        "이미_표명한_입장": session.stance,
        "함께_읽는_것": CORPUS[session.shown[-1]]["work_title"] if session.shown else None,
    }, ensure_ascii=False)
    return _generate(READ_MODEL, READ_SYSTEM, user, READ_SCHEMA, temp=0.2)


# ────────────────────────────────────────────────── ② 정책 (코드가 결정한다)

def control(session: Session, signals: dict) -> tuple[float, float, str]:
    delta = min(.75, .20 + .05 * session.turns)
    if session.turns > 12:
        delta = max(.30, delta - .04 * (session.turns - 12))
    if session.highlights:
        delta = min(.85, delta + .05)

    engagement = signals.get("engagement", "")
    if signals.get("asserted_stance"):
        pi, why = .75, "확신에 찬 판정 → 반대 시점으로 이동"
    elif engagement == "agreeing":
        pi, why = .45, "동의만 반복 → 승인 루프 회피"
    elif signals.get("wants_summary"):
        pi, why = .10, "요약 요구 = 부하 초과 → π 하강, MIP 재산정"
    elif engagement == "resisting":
        pi, why = .55, "저항 — 관여의 신호. 밀되 밀어붙이지 않는다"
    elif engagement == "drifting":
        pi, why = .25, "이탈 조짐 → π 하강"
    else:
        pi, why = .35, "탐색 중 — 중간값"

    cap = min(1.0, .20 + .08 * session.tau)
    if pi > cap:
        why += f" / τ={session.tau} 상한 {cap:.2f} 절삭"
        pi = cap
    return round(delta, 2), round(pi, 2), why


# ────────────────────────────────────────────────── ③④ 검색 + MIP

def retrieve(session: Session, text: str, delta: float, pi: float,
             embeddings: dict, want_appeal: bool) -> list[str]:
    query = _embed(f"{text}\n{session.stance or ''}")
    pool = [sid for sid, s in CORPUS.items() if s["work_id"] == session.room]

    if want_appeal:
        # 관점을 요약하면 허수아비가 된다 — 호소를 감당할 분량만 후보로 둔다
        need = 120 * VQR_FLOOR_APPEAL / (1 - VQR_FLOOR_APPEAL)
        capable = [sid for sid in pool if len(CORPUS[sid]["text_ko"]) >= need]
        pool = capable or pool

    scored = []
    for sid in pool:
        s = CORPUS[sid]
        score = 2.2 * _cos(query, embeddings[sid])          # 의미 유사도
        if sid in session.used[-3:]:
            score -= 1.2                                     # NNI: 방금 쓴 것 회피
        elif sid in session.shown:
            score -= .45
        else:
            score += .55                                     # 진도 전진
        if sid in session.highlights:
            score += .8 * delta                              # δ: 밑줄 회귀
        if pi >= .5 and session.stance_target:
            score += .7 * pi if s.get("viewpoint") == session.stance_target else -.2
        score -= .06 * s.get("difficulty", 2) * (1 if session.tau < 5 else .3)
        scored.append((score, sid))

    scored.sort(reverse=True)
    best = scored[0][1]

    out: list[str] = []

    def add(sid: str) -> None:
        if sid in out:
            return
        for pre in CORPUS[sid].get("prereq_spans", []):
            if pre not in session.shown:
                add(pre)
        out.append(sid)

    add(best)
    return out


# ────────────────────────────────────────────────── ⑤ 쓰기

WRITE_SCHEMA = {"type": "OBJECT", "properties": {
    "frame": {"type": "STRING"},
    "appeal": {"type": "STRING", "description": "정의감 호출. 쓰지 않을 거면 빈 문자열"},
}, "required": ["frame", "appeal"]}

WRITE_SYSTEM = """너는 문학 서비스 「필담」의 문우 에이전트다. 고전 작가의 글을 독자에게 건넨다.

너의 위치:
- 너는 그 작가가 아니다. 물으면 숨기지 말고 그렇게 답한다. 여기서 진짜인 것은 인용되는 문장뿐이다.
- 너는 문학을 쓰지 않는다. 원문을 인용하거나 옮겨 적거나 흉내 내지 않는다.
  작가의 어조로 삶·세상·인간에 대한 잠언을 지어내는 것은 위작이다. 절대 하지 마라.
- 원문은 시스템이 네 말 아래에 따로 보여 준다. 너는 그 옆에 놓일 짧은 문장만 쓴다.

금칙:
- 감정 미러링("그 마음 이해해요"), 작품 평가 형용사("아름다운 문장", "위대한 작품")
- 요약 접속사("요컨대", "정리하자면", "한마디로"), 무해한 균형("물론 반대 의견도 있습니다만")
- 출처 없는 1인칭 내면 고백, 비서 어투("무엇을 도와드릴까요"), 이모지, 느낌표 남발
- 요약 요구를 받아도 줄거리를 요약해 주지 않는다. 요약이 무엇을 잃는지 겨눈다.

문체: 건조하고 단정적이다. 존댓말. 짧을수록 좋다. 설명하지 말고 겨누어라.
독자가 무슨 말을 하든 그 말에 실제로 응답한다. 인사에는 인사로, 물음에는 답으로.
그러나 잡담으로 흐르지 않고 읽기로 돌아온다."""


def write_turn(session: Session, text: str, signals: dict, spans: list[str],
               delta: float, pi: float, want_appeal: bool, attempt: int) -> dict:
    card = CARDS[session.writer]
    quoted = sum(len(CORPUS[s]["text_ko"]) for s in spans)
    budget = max(24, int((0.45 if attempt == 1 else 0.25) * quoted))
    if signals.get("is_small_talk") or signals.get("asks_what_you_are"):
        budget = 140

    user = json.dumps({
        "문우_카드": card,
        "독자_발화": text,
        "독자에게서_읽어_낸_것": signals,
        "직전_대화": session.history[-6:],
        "관계_연령_tau": session.tau,
        "기억_의존도_delta": delta,
        "관점_거리_pi": pi,
        "지금_제시될_원문": [
            {"span_id": s, "작품": CORPUS[s]["work_title"], "위치": CORPUS[s]["locus"],
             "시점": CORPUS[s]["viewpoint"], "감정소득": CORPUS[s].get("income_tags", []),
             "야생성_메모": CORPUS[s].get("wildness_note"),
             "본문": CORPUS[s]["text_ko"]}
            for s in spans
        ] if spans else [],
        "프레임_최대_문자수": budget,
        "정의감_호출_허용": want_appeal,
        "지시": (
            f"프레임은 {budget}자 이내. 원문을 옮겨 적지 마라. "
            + ("정의감 호출을 써라. 감정이 아니라 정의감에 요구하는 어법이다. "
               "다아시의 편지가 그 원형이다." if want_appeal else "appeal은 빈 문자열로 둬라.")
            + (" 지금 독자는 읽기와 무관한 말을 걸었다. 원문이 제시되지 않으니 짧게 받고 읽기로 돌아와라."
               if not spans else "")
        ),
    }, ensure_ascii=False)
    return _generate(WRITE_MODEL, WRITE_SYSTEM, user, WRITE_SCHEMA, temp=1.0)


# ────────────────────────────────────────────────── 턴

def turn(session: Session, text: str, embeddings: dict) -> dict:
    session.turns += 1
    signals = read_reader(session, text)
    if signals.get("asserted_stance"):
        session.stance = signals["asserted_stance"]
        session.stance_target = signals.get("stance_target") or session.stance_target

    delta, pi, why = control(session, signals)
    serve_passage = not (signals.get("is_small_talk") or signals.get("asks_what_you_are"))
    if not serve_passage:
        why = "응대 턴 — 문학적 소득을 주장하지 않으므로 인용이 없다"
    want_appeal = (pi >= .7 and session.tau >= APPEAL_TAU and bool(session.stance)
                   and serve_passage)

    spans = retrieve(session, text, delta, pi, embeddings, want_appeal) if serve_passage else []

    blocks, report, rejected = [], None, None
    for attempt in (1, 2):
        out = write_turn(session, text, signals, spans, delta, pi, want_appeal, attempt)
        frame = (out.get("frame") or "").strip()
        appeal = (out.get("appeal") or "").strip() if want_appeal else ""
        cand = [{"type": "frame", "provenance": "model", "modality": "hypothesis", "text": frame}]
        if appeal:
            cand.append({"type": "appeal", "provenance": "model", "modality": "hypothesis",
                         "text": appeal})
        quotes = [{"type": "quote", "provenance": "source", "modality": "canon", "span_id": s}
                  for s in spans]
        turn_obj = {"turn_id": f"t{session.turns:04d}",
                    "session_type": "reading" if spans else "chrome",
                    "writer_id": session.writer, "tau": session.tau,
                    "delta": delta, "pi": pi, "blocks": cand + quotes}
        report = validate(turn_obj, CORPUS) if spans else _validate_chrome(turn_obj)
        if report.ok:
            blocks = cand + quotes
            break
        rejected = report
    else:
        blocks = [{"type": "quote", "provenance": "source", "modality": "canon", "span_id": s}
                  for s in spans]
        report = validate({"turn_id": "fb", "session_type": "reading", "writer_id": session.writer,
                           "tau": session.tau, "blocks": blocks}, CORPUS) if spans else report

    for sid in spans:
        if sid not in session.shown:
            session.shown.append(sid)
    session.used.extend(spans)
    session.tau += 1
    session.history.append({"독자": text, "문우": next(
        (b["text"] for b in blocks if b["type"] == "frame"), "(원문만 제시)")})

    return {
        "blocks": [_render(b) for b in blocks],
        "gauge": {"delta": delta, "pi": pi, "tau": session.tau,
                  "vqr": round(report.vqr, 2) if report else None,
                  "slp": round(report.slp, 2) if report else None,
                  "why": why, "note": signals.get("note", ""),
                  "served_passage": bool(spans)},
        "notice": ("이 대화의 응답은 AI가 생성합니다. 붉은 칸의 인용문만 원문입니다."
                   if signals.get("asks_what_you_are") else None),
        "fallback": sorted({f.code for f in rejected.findings if f.severity == "error"})
                    if (rejected and not any(b["type"] in ("frame", "appeal") for b in blocks)) else None,
    }


def _validate_chrome(turn_obj: dict):
    """응대 턴: 인용이 없으므로 VQR을 적용하지 않는다. 예산과 금칙 문체만 본다."""
    from validate_response import BANNED_REGISTER, Report, SENTENCE_SPLIT
    import re
    rep = Report()
    text = " ".join(b.get("text", "") for b in turn_obj["blocks"])
    rep.model_chars = len(text)
    if len(text) > 140:
        rep.error("CHROME_BUDGET", f"응대 턴 {len(text)}자 > 140자")
    total = flagged = 0
    for sentence in filter(None, (s.strip() for s in SENTENCE_SPLIT.split(text))):
        total += 1
        for name, pats in BANNED_REGISTER.items():
            if any(re.search(p, sentence) for p in pats):
                flagged += 1
                rep.error("BANNED_REGISTER", f"금칙 문체 [{name}] — \"{sentence[:30]}…\"")
                break
    rep.slp = flagged / total if total else 0.0
    rep.vqr = 0.0
    return rep


def _render(block: dict) -> dict:
    if block["type"] != "quote":
        return block
    s = CORPUS[block["span_id"]]
    return {"type": "quote", "span_id": block["span_id"], "work_title": s["work_title"],
            "locus": s["locus"], "text_ko": s["text_ko"], "text_src": s["text_src"]}
