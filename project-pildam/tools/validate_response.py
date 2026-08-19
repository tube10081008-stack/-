#!/usr/bin/env python3
"""필담 응답 계약 검증기.

specs/response-contract.md 의 규칙을 집행한다. 모델 출력은 인용문의 텍스트를
담지 않으며 span_id 만 담는다 — 인용 텍스트는 코퍼스에서 materialize 된다.
따라서 인용 환각은 검사 대상이 아니라 구조적으로 불가능하다.

사용:
    python3 validate_response.py --self-test
    python3 validate_response.py --corpus corpus.json --turn turn.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field

# ---------------------------------------------------------------- 계약 상수

VQR_FLOOR = {"reading": 0.60, "dialogue": 0.35}
VQR_FLOOR_APPEAL = 0.75
FRAME_BUDGET_CHARS = 400
FRAME_RATIO_READING = 0.8          # reading 세션: 모델 저작 ≤ 0.8 × 인용 문자수
APPEAL_TAU_THRESHOLD = 10

MODEL_BLOCKS = {"frame", "appeal", "contrast"}

BANNED_REGISTER = {
    "mirroring": [
        r"(마음|심정)[이을]?\s*(충분히\s*)?(이해|공감)",
        r"(슬프|힘드|괴로우|외로우)시겠",
        r"얼마나\s*(힘드|슬프|괴로우)",
    ],
    "evaluative": [
        r"(위대한|아름다운|훌륭한|멋진)\s*(작품|문장|글|대목|구절)",
        r"명작(이|입니다|이죠)",
        r"감동적인\s*(장면|대목)",
    ],
    "summarizing": [
        r"요컨대", r"정리하자면", r"한마디로", r"간단히\s*말(하면|해서)",
        r"쉽게\s*말(하면|해서)", r"줄거리를\s*(요약|정리)",
    ],
    "fabricated_interiority": [
        r"(저는|나는)\s*(그때|당시)[^.。!?]*?(두려웠|슬펐|기뻤|괴로웠|외로웠)",
        r"내\s*마음\s*속에서는[^.。!?]*?(했|였)습니다",
    ],
    "counterfeit": [
        # 모델이 작가의 어조로 삶·세상·인간에 대한 일반 명제를 단정하면 그것은 위작이다 (L1).
        # 정규식은 이 부류를 전부 잡지 못한다 — 사람의 검수가 함께 필요하다.
        r"(인생|삶|세상\s*만사|세상|인간)(은|이란|이라는)\s*[^.。!?]{0,24}(입니다|이다|이지요)",
        r"(모든\s*것|만물)(은|이)\s*[^.。!?]{0,20}(입니다|이다)",
    ],
    "harmless_balance": [
        r"물론\s*반대\s*(의견|견해)도",
        r"(양쪽|둘\s*다)\s*일리가\s*있",
        r"어느\s*쪽도\s*틀리지\s*않",
    ],
}

# 문우별 시대착오 어휘. 실서비스에서는 카드에서 주입한다.
ANACHRONISM = {
    "_default": [r"인터넷", r"스마트폰", r"이메일", r"알고리즘", r"데이터베이스"],
}

SENTENCE_SPLIT = re.compile(r"[.。!?…]+\s*")


@dataclass
class Finding:
    severity: str            # "error" | "warn"
    code: str
    message: str


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    quoted_chars: int = 0
    model_chars: int = 0
    vqr: float = 0.0
    slp: float = 0.0

    @property
    def ok(self) -> bool:
        return not any(f.severity == "error" for f in self.findings)

    def error(self, code: str, message: str) -> None:
        self.findings.append(Finding("error", code, message))

    def warn(self, code: str, message: str) -> None:
        self.findings.append(Finding("warn", code, message))


# ---------------------------------------------------------------- 검사기

def _check_provenance(block: dict, idx: int, rep: Report) -> None:
    """L1 / 논문의 모델 강등: 모델 저작 블록은 캐논이 될 수 없다."""
    prov, mod = block.get("provenance"), block.get("modality")
    if prov is None or mod is None:
        rep.error("PROV_MISSING", f"블록 {idx}: provenance/modality 태그 없음 — 저장 불가")
        return
    if prov == "model" and mod == "canon":
        rep.error("MODEL_CANON",
                  f"블록 {idx}: 모델 저작 블록이 캐논으로 표기됨 (L1 위반)")
    if block.get("type") == "quote" and prov != "source":
        rep.error("QUOTE_PROV", f"블록 {idx}: quote 블록의 provenance는 source여야 함")


def _check_quote(block: dict, idx: int, corpus: dict, rep: Report) -> int:
    """인용 블록: 텍스트를 담지 않아야 하고, span이 코퍼스에 존재해야 한다."""
    if "text" in block:
        rep.error("QUOTE_TEXT_INLINE",
                  f"블록 {idx}: 모델이 인용문 텍스트를 출력함 — span_id만 허용 (L1 위반)")
    span_id = block.get("span_id")
    if not span_id:
        rep.error("SPAN_MISSING", f"블록 {idx}: span_id 없음")
        return 0
    span = corpus.get(span_id)
    if span is None:
        rep.error("SPAN_UNKNOWN", f"블록 {idx}: 코퍼스에 없는 span_id '{span_id}'")
        return 0
    return len(span.get("text_ko") or span.get("text_src") or "")


def _check_mip(blocks: list[dict], corpus: dict, rep: Report) -> None:
    """L2: 선행 span을 요구하는 인용은 선행 span과 함께 제시되어야 한다."""
    cited = {b.get("span_id") for b in blocks if b.get("type") == "quote"}
    for span_id in list(cited):
        span = corpus.get(span_id)
        if not span or span.get("mip_class") != "requires_prereq":
            continue
        missing = [p for p in span.get("prereq_spans", []) if p not in cited]
        if missing:
            rep.error("MIP_VIOLATION",
                      f"span '{span_id}'는 선행 span {missing}을 요구함 — MIP 미만 응답 (L2 위반)")


def _model_text(block: dict) -> str:
    if block.get("type") == "contrast":
        return block.get("paraphrase", "")
    return block.get("text", "")


def _check_register(blocks: list[dict], writer_id: str, rep: Report) -> None:
    """금칙 문체 검사 및 SLP 산출."""
    patterns = {k: [re.compile(p) for p in v] for k, v in BANNED_REGISTER.items()}
    patterns["anachronism"] = [
        re.compile(p) for p in ANACHRONISM.get(writer_id, ANACHRONISM["_default"])
    ]

    total, flagged = 0, 0
    for idx, block in enumerate(blocks):
        if block.get("type") not in MODEL_BLOCKS:
            continue
        for sentence in filter(None, (s.strip() for s in SENTENCE_SPLIT.split(_model_text(block)))):
            total += 1
            hits = [name for name, pats in patterns.items()
                    if any(p.search(sentence) for p in pats)]
            if hits:
                flagged += 1
                rep.error("BANNED_REGISTER",
                          f"블록 {idx}: 금칙 문체 {hits} — \"{sentence[:40]}…\"")
    rep.slp = flagged / total if total else 0.0


def _check_appeal(turn: dict, blocks: list[dict], rep: Report) -> bool:
    """정의감 호출: τ 임계를 넘어야 한다 (H1′ — 높은 π는 벌어야 한다)."""
    has_appeal = any(b.get("type") == "appeal" for b in blocks)
    if has_appeal and turn.get("tau", 0) < APPEAL_TAU_THRESHOLD:
        rep.error("APPEAL_TOO_EARLY",
                  f"정의감 호출에 τ={turn.get('tau')} — 임계 {APPEAL_TAU_THRESHOLD} 미만 (이탈 위험)")
    return has_appeal


def validate(turn: dict, corpus: dict) -> Report:
    rep = Report()
    blocks = turn.get("blocks", [])
    if not blocks:
        rep.error("EMPTY_TURN", "블록이 없음")
        return rep

    for idx, block in enumerate(blocks):
        _check_provenance(block, idx, rep)
        if block.get("type") == "quote":
            rep.quoted_chars += _check_quote(block, idx, corpus, rep)
        elif block.get("type") in MODEL_BLOCKS:
            rep.model_chars += len(_model_text(block))

    _check_mip(blocks, corpus, rep)
    _check_register(blocks, turn.get("writer_id", "_default"), rep)
    has_appeal = _check_appeal(turn, blocks, rep)

    # VQR
    denominator = rep.quoted_chars + rep.model_chars
    rep.vqr = rep.quoted_chars / denominator if denominator else 0.0
    session_type = turn.get("session_type", "dialogue")
    floor = VQR_FLOOR_APPEAL if has_appeal else VQR_FLOOR.get(session_type, VQR_FLOOR["dialogue"])
    if rep.vqr < floor:
        rep.error("VQR_FLOOR",
                  f"VQR {rep.vqr:.2f} < 하한 {floor:.2f} "
                  f"(인용 {rep.quoted_chars}자 / 모델 {rep.model_chars}자)")

    # 프레임 예산
    if rep.model_chars > FRAME_BUDGET_CHARS:
        rep.error("FRAME_BUDGET",
                  f"모델 저작 {rep.model_chars}자 > 예산 {FRAME_BUDGET_CHARS}자")
    if session_type == "reading" and rep.model_chars > FRAME_RATIO_READING * rep.quoted_chars:
        rep.error("FRAME_RATIO",
                  f"reading 세션에서 모델 저작 {rep.model_chars}자 > "
                  f"0.8 × 인용 {rep.quoted_chars}자")

    if 0 < rep.vqr < floor + 0.05:
        rep.warn("VQR_MARGIN", "VQR이 하한에 근접 — 인용 확장 권장")
    return rep


# ---------------------------------------------------------------- 자체 시험

SELF_TEST_CORPUS = {
    # 공유 저작물 원문 + 자체 번역 예시 (실제 서비스 코퍼스가 아님)
    "shakespeare.son18.s001": {
        "text_src": "Shall I compare thee to a summer's day?\n"
                    "Thou art more lovely and more temperate:",
        "text_ko": "그대를 여름날에 견주어 볼까요?\n그대가 더 사랑스럽고 더 온화합니다.",
        "mip_class": "standalone",
        "translator_id": "tr_sample",
    },
    "austen.pp.v2.c12.s001": {
        "text_src": "(샘플 픽스처 — 실제 원문 아님. 계약 검증 로직 시험용 자리표시자입니다. "
                    "실서비스 코퍼스에는 저본 대조를 마친 원문과 자체 번역이 들어갑니다.)",
        "text_ko": "(샘플 픽스처 — 실제 원문 아님. 계약 검증 로직 시험용 자리표시자입니다. "
                   "실서비스 코퍼스에는 저본 대조를 마친 원문과 자체 번역이 들어갑니다.)",
        "mip_class": "requires_prereq",
        "prereq_spans": ["austen.pp.v2.c11.s009"],
    },
    "austen.pp.v2.c11.s009": {
        "text_ko": "(샘플 픽스처 — 선행 span 자리표시자. 실제 원문 아님.)",
        "mip_class": "standalone",
    },
}

VALID_TURN = {
    "turn_id": "t_ok", "session_type": "reading", "writer_id": "shakespeare",
    "tau": 24, "delta": 0.4, "pi": 0.3,
    "blocks": [
        {"type": "frame", "provenance": "model", "modality": "hypothesis",
         "text": "어제 이 행을 과장이라 하셨지요."},
        {"type": "quote", "provenance": "source", "modality": "canon",
         "span_id": "shakespeare.son18.s001"},
    ],
}

BAD_TURNS = {
    "모델 저작이 캐논으로 표기됨": {
        "turn_id": "t_bad1", "session_type": "reading", "writer_id": "shakespeare", "tau": 20,
        "blocks": [
            {"type": "frame", "provenance": "model", "modality": "canon", "text": "짧게."},
            {"type": "quote", "provenance": "source", "modality": "canon",
             "span_id": "shakespeare.son18.s001"},
        ],
    },
    "모델이 인용문 텍스트를 직접 출력": {
        "turn_id": "t_bad2", "session_type": "reading", "writer_id": "shakespeare", "tau": 20,
        "blocks": [
            {"type": "quote", "provenance": "source", "modality": "canon",
             "span_id": "shakespeare.son18.s001",
             "text": "그대를 여름날에 견주어 볼까요? (모델이 지어낸 판본)"},
        ],
    },
    "금칙 문체 — 미끄러움": {
        "turn_id": "t_bad3", "session_type": "reading", "writer_id": "shakespeare", "tau": 20,
        "blocks": [
            {"type": "frame", "provenance": "model", "modality": "hypothesis",
             "text": "그 마음 충분히 이해해요. 요컨대 이건 정말 아름다운 문장이죠."},
            {"type": "quote", "provenance": "source", "modality": "canon",
             "span_id": "shakespeare.son18.s001"},
        ],
    },
    "VQR 하한 미달": {
        "turn_id": "t_bad4", "session_type": "reading", "writer_id": "shakespeare", "tau": 20,
        "blocks": [
            {"type": "frame", "provenance": "model", "modality": "hypothesis",
             "text": "이 소네트가 말하려는 바를 제 방식으로 풀어 보겠습니다. " + "설명을 이어갑니다. " * 12},
            {"type": "quote", "provenance": "source", "modality": "canon",
             "span_id": "shakespeare.son18.s001"},
        ],
    },
    "MIP 위반 — 선행 span 누락": {
        "turn_id": "t_bad5", "session_type": "reading", "writer_id": "austen", "tau": 20,
        "blocks": [
            {"type": "frame", "provenance": "model", "modality": "hypothesis", "text": "읽어 주십시오."},
            {"type": "quote", "provenance": "source", "modality": "canon",
             "span_id": "austen.pp.v2.c12.s001"},
        ],
    },
    "정의감 호출이 너무 이름": {
        "turn_id": "t_bad6", "session_type": "reading", "writer_id": "austen", "tau": 3,
        "blocks": [
            {"type": "appeal", "provenance": "model", "modality": "hypothesis",
             "text": "당신의 정의감에 요구합니다."},
            {"type": "quote", "provenance": "source", "modality": "canon",
             "span_id": "austen.pp.v2.c11.s009"},
        ],
    },
}


def _print(report: Report, label: str) -> None:
    status = "PASS" if report.ok else "FAIL"
    print(f"[{status}] {label}  VQR={report.vqr:.2f}  SLP={report.slp:.2f}")
    for f in report.findings:
        print(f"        {f.severity.upper():5s} {f.code}: {f.message}")


def self_test() -> int:
    print("=== 유효한 턴 (통과해야 함) ===")
    ok_report = validate(VALID_TURN, SELF_TEST_CORPUS)
    _print(ok_report, "정상 턴")

    print("\n=== 계약 위반 턴 (전부 기각되어야 함) ===")
    all_rejected = True
    for label, turn in BAD_TURNS.items():
        rep = validate(turn, SELF_TEST_CORPUS)
        _print(rep, label)
        all_rejected &= not rep.ok

    print()
    if ok_report.ok and all_rejected:
        print("자체 시험 통과: 정상 턴 1건 승인, 위반 턴 6건 전부 기각.")
        return 0
    print("자체 시험 실패.")
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description="필담 응답 계약 검증기")
    ap.add_argument("--self-test", action="store_true", help="내장 픽스처로 계약 규칙을 시험한다")
    ap.add_argument("--corpus", help="span_id → span 메타데이터 JSON")
    ap.add_argument("--turn", help="검증할 턴 JSON")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    if not (args.corpus and args.turn):
        ap.error("--self-test 또는 --corpus 와 --turn 을 함께 지정하십시오")

    with open(args.corpus, encoding="utf-8") as f:
        corpus = json.load(f)
    with open(args.turn, encoding="utf-8") as f:
        turn = json.load(f)

    rep = validate(turn, corpus)
    _print(rep, turn.get("turn_id", "turn"))
    return 0 if rep.ok else 1


if __name__ == "__main__":
    sys.exit(main())
