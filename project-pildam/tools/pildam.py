#!/usr/bin/env python3
"""필담 대화 프로토타입.

04장의 파이프라인을 그대로 구현한다:
  ① 독서 상태 갱신 → ② (δ, π) 컨트롤러 → ③ 조건부 검색 → ④ MIP 확장
  → ⑤ 프레임 생성 → ⑥ 계약 검증 → ⑦ 렌더링

핵심: ⑤에서 어떤 엔진을 쓰든 모델은 **인용문 텍스트를 만들지 않는다.** span_id만 고른다.
      인용문은 ⑦에서 코퍼스로부터 materialize 된다.

엔진:
  mock    — 결정론적. API 키 불필요. 파이프라인 전체를 보여준다.
  claude  — Anthropic Messages API가 ⑤ 프레임만 생성한다. ANTHROPIC_API_KEY 필요.

실행:
  python3 pildam.py --demo
  python3 pildam.py                         # 대화 모드
  python3 pildam.py --engine claude
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_response import validate  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CORPUS = ROOT / "corpus" / "sample.json"
VERIFICATION_RANK = {"placeholder": 0, "self_attested": 1, "sourced": 2}

C = {"dim": "\033[2m", "b": "\033[1m", "q": "\033[36m", "m": "\033[33m",
     "warn": "\033[31m", "ok": "\033[32m", "r": "\033[0m"}


# ------------------------------------------------------------------ 상태

@dataclass
class ReadingState:
    """계층 II — 독서 상태 S_t."""
    work_id: str
    progress: float = 0.0
    open_questions: list[str] = field(default_factory=list)
    stance: str | None = None            # R_t — 독자가 표명한 판정
    stance_confidence: float = 0.0
    stance_viewpoint: str | None = None  # 그 판정이 향한 인물
    highlights: list[str] = field(default_factory=list)   # B_t
    used_spans: list[str] = field(default_factory=list)
    turns: int = 0
    tau: int = 0                          # 관계 연령 (세션 수)


# ------------------------------------------------------------------ ① 의도 분류

INTENT_PATTERNS = [
    ("summary_request", [r"요약", r"줄거리", r"정리해\s*줘", r"간단히", r"짧게\s*말"]),
    ("verdict",         [r"(오만|무책임|이기적|비겁|한심|위선|틀렸|나쁘|겁쟁이|우유부단)",
                         r"(이|가)\s*싫", r"공감\s*안"]),
    ("agree",           [r"^(맞아|그러네|그렇네|동의|응$|그런\s*것\s*같아)"]),
    ("highlight",       [r"^/밑줄", r"(이\s*문장|이\s*구절).*(좋|남기|저장)"]),
    ("question",        [r"\?$", r"왜", r"뭐(야|지)", r"어떻게"]),
]


def classify(text: str) -> str:
    for intent, pats in INTENT_PATTERNS:
        if any(re.search(p, text) for p in pats):
            return intent
    return "continue"


VIEWPOINT_HINTS = {"햄릿": ["햄릿", "왕자"], "화자": ["화자", "시인"], "다아시": ["다아시"],
                   "엘리자베스": ["엘리자베스", "리지"]}


def detect_target(text: str) -> str | None:
    for vp, hints in VIEWPOINT_HINTS.items():
        if any(h in text for h in hints):
            return vp
    return None


# ------------------------------------------------------------------ ② 컨트롤러

def controller(state: ReadingState, intent: str) -> tuple[float, float, str]:
    """(δ, π)를 결정하고 이유를 함께 돌려준다. 02장 2.4절."""
    # δ: 형성기에 상승, 유지기에 하강 (논문 H1)
    delta = min(0.75, 0.20 + 0.05 * state.turns)
    if state.turns > 12:
        delta = max(0.30, delta - 0.04 * (state.turns - 12))
    if state.highlights:
        delta = min(0.85, delta + 0.05)

    # π: 기본 낮음. 판정에는 올리고, 승인 루프에도 올리고, 요약 요구에는 내린다.
    pi, why = 0.20, "기본값"
    if intent == "verdict":
        pi, why = 0.75, "독자가 확신에 찬 판정을 표명함 → 반대 시점으로 이동"
    elif intent == "agree":
        pi, why = 0.45, "동의만 반복됨 → 승인 루프 회피"
    elif intent == "summary_request":
        pi, why = 0.10, "요약 요구 = 부하 초과 신호 → π 하강, MIP 재산정"
    elif intent == "question":
        pi, why = 0.35, "질문 — 중간값"

    # H1′: 높은 π는 벌어야 한다. τ가 상한을 만든다.
    cap = min(1.0, 0.20 + 0.08 * state.tau)
    if pi > cap:
        why += f" / τ={state.tau} 상한 {cap:.2f}로 절삭"
        pi = cap
    return round(delta, 2), round(pi, 2), why


# ------------------------------------------------------------------ ③ 검색 + ④ MIP

def retrieve(corpus: dict, state: ReadingState, intent: str, delta: float, pi: float,
             min_verification: str, intent_text: str = "") -> tuple[list[str], str]:
    floor = VERIFICATION_RANK[min_verification]
    skipped_unverified = []
    scored = []

    for sid, span in corpus.items():
        if span.get("work_id") != state.work_id:
            continue
        if VERIFICATION_RANK.get(span.get("verified", "placeholder"), 0) < floor:
            skipped_unverified.append(sid)
            continue

        score = 0.0
        # NNI: 최근 쓴 span은 감점 (같은 구절을 같은 각도로 두 번 내밀지 않는다)
        if sid in state.used_spans[-4:]:
            score -= 2.0
        # δ: 기억 의존도가 높으면 독자가 밑줄 그은 것을 다시 꺼낸다
        if sid in state.highlights:
            score += 2.0 * delta
        # π: 관점 거리가 크면 독자의 판정이 향한 인물의 시점을 고른다
        if pi >= 0.5 and state.stance_viewpoint:
            score += 2.5 * pi if span.get("viewpoint") == state.stance_viewpoint else -0.5
        # 어휘 일치: 독자가 지목한 대목(태그·위치)을 우선한다
        haystack = " ".join(span.get("income_tags", []) + [span.get("locus", "")])
        if any(tok and tok in haystack for tok in re.findall(r"[가-힣]{2,}", intent_text)):
            score += 1.5
        # 난이도: 입문기 보호
        score -= 0.15 * span.get("difficulty", 2) * (1.0 if state.tau < 5 else 0.3)
        scored.append((score, sid))

    scored.sort(reverse=True)
    picked = [sid for _, sid in scored[:1]]
    picked = expand_mip(picked, corpus)      # ④ MIP — 자르지 않고 확장한다
    note = ""
    if skipped_unverified:
        note = f"검증 미달로 제외된 span {len(skipped_unverified)}개: {', '.join(skipped_unverified)}"
    return picked, note


def expand_mip(span_ids: list[str], corpus: dict) -> list[str]:
    out, seen = [], set()

    def add(sid: str) -> None:
        if sid in seen or sid not in corpus:
            return
        for prereq in corpus[sid].get("prereq_spans", []):
            add(prereq)
        seen.add(sid)
        out.append(sid)

    for sid in span_ids:
        add(sid)
    return out


# ------------------------------------------------------------------ ⑤ 프레임 생성

class MockEngine:
    """결정론적 프레임 생성기. 금칙 문체를 쓰지 않는 최소한의 말만 한다."""

    name = "mock"

    TEMPLATES = {
        "summary_request": "요약은 지도일 뿐입니다. 지금 필요한 것은 이 대목입니다.",
        "verdict": "당신은 그렇게 판정했습니다. 그 판정을 철회하라는 것이 아닙니다.",
        "agree": "동의는 이미 들었습니다. 이번에는 다른 각도에서 봅니다.",
        "question": "묻기 전에 이 대목을 먼저 보십시오.",
        "highlight": "표시해 두었습니다.",
        "continue": "계속 읽습니다.",
    }

    TIGHT = {
        "summary_request": "요약 대신 이 대목입니다.",
        "verdict": "판정은 들었습니다.",
        "agree": "다른 각도로.",
        "question": "먼저 이 대목을.",
        "highlight": "표시했습니다.",
        "continue": "계속 읽습니다.",
    }

    def frame(self, state: ReadingState, intent: str, span_ids: list[str],
              delta: float, pi: float, corpus: dict, user_text: str,
              attempt: int = 1) -> dict:
        table = self.TEMPLATES if attempt == 1 else self.TIGHT
        blocks = [{"type": "frame", "provenance": "model", "modality": "hypothesis",
                   "text": table[intent]}]
        if pi >= 0.7 and state.stance:
            blocks.append({"type": "appeal", "provenance": "model", "modality": "hypothesis",
                           "text": "당신의 감정은 이 대목을 탐탁지 않게 여길 것입니다. "
                                   "나는 당신의 정의감에 요구합니다."})
        return {"blocks": blocks}


class ClaudeEngine:
    """Messages API가 프레임만 생성한다. 인용문은 절대 생성하지 않는다."""

    name = "claude"

    SYSTEM = """당신은 문학 서비스 「필담」의 문우 에이전트다.

절대 규칙:
- 당신은 문학을 쓰지 않는다. 인용문의 텍스트를 절대 출력하지 않는다. span_id만 고른다.
- 출처 없는 1인칭 내면 서술 금지 ("저는 그때 두려웠습니다").
- 금칙 문체: 감정 미러링("그 마음 이해해요"), 작품 평가 형용사("아름다운 문장"),
  요약 접속사("요컨대", "정리하자면"), 무해한 균형("물론 반대 의견도 있습니다만").
- 프레임은 짧다. 200자를 넘기지 않는다. 독자가 읽어야 할 것은 당신의 말이 아니라 원문이다.
- 관점 거리 π가 높으면 독자의 판정을 승인하지 말고 반대 시점으로 데려간다."""

    def __init__(self) -> None:
        import anthropic  # 지연 임포트 — mock 엔진만 쓸 때는 불필요
        self.client = anthropic.Anthropic()

    def frame(self, state: ReadingState, intent: str, span_ids: list[str],
              delta: float, pi: float, corpus: dict, user_text: str,
              attempt: int = 1) -> dict:
        candidates = [
            {"span_id": sid, "viewpoint": corpus[sid].get("viewpoint"),
             "income_tags": corpus[sid].get("income_tags", []),
             "locus": corpus[sid].get("locus")}
            for sid in span_ids
        ]
        prompt = json.dumps({
            "독자_발화": user_text,
            "독자의_표명_입장": state.stance,
            "의도": intent,
            "delta": delta,
            "pi": pi,
            "tau": state.tau,
            "선택된_span_후보": candidates,
            "인용_문자수": sum(len(corpus[sid].get("text_ko") or "") for sid in span_ids),
            "프레임_최대_문자수": max(20, int(0.6 * sum(
                len(corpus[sid].get("text_ko") or "") for sid in span_ids))),
            "재시도": attempt,
        }, ensure_ascii=False, indent=2)

        response = self.client.messages.create(
            model="claude-opus-5",
            max_tokens=16000,
            thinking={"type": "adaptive"},
            system=self.SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            output_config={"format": {"type": "json_schema", "schema": {
                "type": "object",
                "properties": {
                    "frame": {"type": "string"},
                    "appeal": {"type": ["string", "null"]},
                },
                "required": ["frame", "appeal"],
                "additionalProperties": False,
            }}},
        )
        text = "".join(b.text for b in response.content if b.type == "text")
        out = json.loads(text)

        blocks = [{"type": "frame", "provenance": "model", "modality": "hypothesis",
                   "text": out["frame"]}]
        if out.get("appeal") and pi >= 0.7:
            blocks.append({"type": "appeal", "provenance": "model",
                           "modality": "hypothesis", "text": out["appeal"]})
        return {"blocks": blocks}


# ------------------------------------------------------------------ ⑥⑦ 조립 · 검증 · 렌더링

def build_turn(state: ReadingState, engine, intent: str, span_ids: list[str],
               delta: float, pi: float, corpus: dict, user_text: str) -> tuple[dict, object, int]:
    """계약을 통과할 때까지 최대 2회 재생성하고, 실패하면 인용 단독으로 폴백한다."""
    quotes = [{"type": "quote", "provenance": "source", "modality": "canon", "span_id": sid}
              for sid in span_ids]
    last_report = None
    for attempts in (1, 2):
        generated = engine.frame(state, intent, span_ids, delta, pi, corpus,
                                 user_text, attempt=attempts)
        turn = {"turn_id": f"t{state.turns:04d}", "session_type": "reading",
                "writer_id": "shakespeare", "tau": state.tau, "delta": delta, "pi": pi,
                "blocks": generated["blocks"] + quotes}
        report = validate(turn, corpus)
        last_report = report
        if report.ok:
            return turn, report, attempts
    # 폴백: 말할 것이 없으면 원문만 내민다
    turn = {"turn_id": f"t{state.turns:04d}", "session_type": "reading",
            "writer_id": "shakespeare", "tau": state.tau, "delta": delta, "pi": pi,
            "blocks": quotes}
    return turn, validate(turn, corpus), last_report


def render(turn: dict, corpus: dict, report, why: str, note: str,
           rejected) -> None:
    print()
    for block in turn["blocks"]:
        if block["type"] == "quote":
            span = corpus[block["span_id"]]
            head = f"{span['work_title']} · {span['locus']}"
            flags = []
            if span.get("verified") != "sourced":
                flags.append(f"검증={span.get('verified')}")
            if span.get("translation_status") == "sample_pending_human":
                flags.append("번역=샘플(인간 확정 전)")
            print(f"  {C['dim']}[원문] {head}"
                  + (f"  {' · '.join(flags)}" if flags else "") + C["r"])
            for line in (span.get("text_ko") or "").split("\n"):
                print(f"  {C['q']}{line}{C['r']}")
            for line in (span.get("text_src") or "").split("\n"):
                print(f"  {C['dim']}{line}{C['r']}")
            print()
        else:
            tag = "정의감 호출" if block["type"] == "appeal" else "모델"
            print(f"  {C['m']}[{tag}] {block['text']}{C['r']}")
    if rejected is not None:
        codes = sorted({f.code for f in rejected.findings if f.severity == "error"})
        print(f"  {C['warn']}[폴백] 프레임이 계약을 통과하지 못했습니다 ({', '.join(codes)}). "
              f"원문만 제시합니다.{C['r']}")
        if "VQR_FLOOR" in codes and turn["pi"] >= 0.7:
            print(f"  {C['warn']}       정의감 호출은 VQR 0.75를 요구합니다. "
                  f"이 span이 MIP 미만입니다 — 관점을 요약하면 허수아비가 되기 때문입니다.{C['r']}")
    if note:
        print(f"  {C['warn']}[코퍼스] {note}{C['r']}")
    print(f"  {C['dim']}δ={turn['delta']}  π={turn['pi']}  τ={turn['tau']}  "
          f"VQR={report.vqr:.2f}  SLP={report.slp:.2f}  |  {why}{C['r']}")


# ------------------------------------------------------------------ 루프

def step(state: ReadingState, engine, corpus: dict, user_text: str,
         min_verification: str) -> None:
    state.turns += 1
    intent = classify(user_text)                                   # ①
    if intent == "verdict":
        state.stance = user_text
        state.stance_confidence = 0.8
        state.stance_viewpoint = detect_target(user_text) or state.stance_viewpoint
    delta, pi, why = controller(state, intent)                     # ②
    span_ids, note = retrieve(corpus, state, intent, delta, pi,
                              min_verification, user_text)                    # ③④

    if not span_ids:
        print(f"\n  {C['warn']}[코퍼스] 제시할 수 있는 span이 없습니다. "
              f"{note or '해당 작품의 검증된 span 부재.'}{C['r']}")
        print(f"  {C['dim']}요약으로 대체하지 않습니다 (L2).{C['r']}")
        return

    turn, report, rejected = build_turn(state, engine, intent, span_ids,
                                        delta, pi, corpus, user_text)   # ⑤⑥
    has_frame = any(b["type"] in ("frame", "appeal") for b in turn["blocks"])
    render(turn, corpus, report, why, note, None if has_frame else rejected)   # ⑦
    state.used_spans.extend(span_ids)
    if intent == "highlight":
        state.highlights.extend(span_ids)


DEMO_SCRIPT = [
    ("소네트 18 읽고 싶어", "입문 — τ가 낮아 π 상한이 걸린다"),
    ("햄릿은 우유부단한 겁쟁이야", "판정 표명 → π 상승 시도, 그러나 τ 상한에 절삭"),
    ("이 구절 밑줄 긋고 싶어", "밑줄 → B_t 갱신, 이후 δ가 이것을 다시 꺼낸다"),
    ("그냥 줄거리 요약해줘", "요약 요구 → 요약하지 않고 MIP 제시, π 하강"),
    ("맞아 그러네", "동의만 반복 → 승인 루프 회피로 π 재상승"),
]


def run_demo(engine, corpus: dict, min_verification: str) -> None:
    state = ReadingState(work_id="shakespeare.sonnet18", tau=2)
    print(f"{C['b']}=== 필담 데모 · 엔진={engine.name} · "
          f"최소 검증등급={min_verification} ==={C['r']}")
    for text, label in DEMO_SCRIPT:
        print(f"\n{C['b']}독자>{C['r']} {text}   {C['dim']}({label}){C['r']}")
        if "햄릿" in text:
            state.work_id = "shakespeare.hamlet"
        elif "소네트" in text:
            state.work_id = "shakespeare.sonnet18"
        step(state, engine, corpus, text, min_verification)

    print(f"\n{C['b']}--- τ를 24로 올리고 같은 판정을 다시 ---{C['r']}")
    state.tau, state.work_id = 24, "shakespeare.hamlet"
    print(f"\n{C['b']}독자>{C['r']} 햄릿은 우유부단한 겁쟁이야   "
          f"{C['dim']}(동일 발화, τ만 다름 → H1′ 검증){C['r']}")
    step(state, engine, corpus, "햄릿은 우유부단한 겁쟁이야", min_verification)

    print(f"\n{C['b']}--- τ=24, 소네트 결구: MIP 확장 ---{C['r']}")
    state.work_id = "shakespeare.sonnet18"
    print(f"\n{C['b']}독자>{C['r']} 이 시의 결구가 궁금해   "
          f"{C['dim']}(결구는 requires_prereq → 선행 span이 자동 동반){C['r']}")
    step(state, engine, corpus, "이 시의 결구가 궁금해", min_verification)

    print(f"\n{C['b']}--- 오만과 편견: 저본 미확보 작품 ---{C['r']}")
    state.work_id = "austen.pride_and_prejudice"
    print(f"\n{C['b']}독자>{C['r']} 다아시는 오만해   "
          f"{C['dim']}(placeholder span만 존재 → L3가 인용을 거부){C['r']}")
    step(state, engine, corpus, "다아시는 오만해", min_verification)


def repl(engine, corpus: dict, min_verification: str, work_id: str) -> None:
    state = ReadingState(work_id=work_id, tau=2)
    print(f"{C['b']}필담 · 엔진={engine.name}{C['r']}  "
          f"{C['dim']}/state /tau <n> /work <id> /quit{C['r']}")
    while True:
        try:
            text = input(f"\n{C['b']}독자>{C['r']} ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not text:
            continue
        if text == "/quit":
            return
        if text == "/state":
            print(f"  {C['dim']}{state}{C['r']}")
            continue
        if text.startswith("/tau "):
            state.tau = int(text.split()[1])
            print(f"  {C['dim']}τ={state.tau}{C['r']}")
            continue
        if text.startswith("/work "):
            state.work_id = text.split(maxsplit=1)[1]
            print(f"  {C['dim']}work={state.work_id}{C['r']}")
            continue
        step(state, engine, corpus, text, min_verification)


def main() -> int:
    ap = argparse.ArgumentParser(description="필담 대화 프로토타입")
    ap.add_argument("--engine", choices=["mock", "claude"], default="mock")
    ap.add_argument("--corpus", default=str(DEFAULT_CORPUS))
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--work", default="shakespeare.sonnet18")
    ap.add_argument("--min-verification", choices=list(VERIFICATION_RANK),
                    default="self_attested",
                    help="이 등급 미만의 span은 인용하지 않는다 (L3). 실서비스 기본값은 sourced")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args()

    if args.no_color or not sys.stdout.isatty():
        for k in C:
            C[k] = ""

    corpus = json.load(open(args.corpus, encoding="utf-8"))["spans"]
    engine = ClaudeEngine() if args.engine == "claude" else MockEngine()

    if args.min_verification != "sourced":
        print(f"{C['warn']}⚠ 최소 검증등급이 '{args.min_verification}'입니다. "
              f"저본 대조를 마치지 않은 텍스트가 인용될 수 있습니다 (L3 완화 모드).{C['r']}")

    if args.demo:
        run_demo(engine, corpus, args.min_verification)
    else:
        repl(engine, corpus, args.min_verification, args.work)
    return 0


if __name__ == "__main__":
    sys.exit(main())
