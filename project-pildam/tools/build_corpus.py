#!/usr/bin/env python3
"""저본 텍스트 파일 → span 코퍼스.

원문은 자르지 않고 **호흡 단위**로 묶는다(04장 4.3절). 고정 토큰 청킹은 금지다.
저본 파일의 SHA-256을 각 span에 남겨, 어떤 파일에서 나온 텍스트인지 감사할 수 있게 한다.
이 스크립트가 만든 span만 verified="sourced" 를 받는다.

사용:
    python3 build_corpus.py --input hamlet.txt --work-id shakespeare.hamlet \\
        --title 햄릿 --lang en --out corpus/hamlet.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

PARAGRAPH = re.compile(r"\n\s*\n+")


def segment(text: str, max_chars: int) -> list[str]:
    """빈 줄로 나뉜 덩어리를 유지하되, 지나치게 긴 것만 문장 경계에서 나눈다."""
    spans: list[str] = []
    for block in PARAGRAPH.split(text.strip()):
        block = block.strip()
        if not block:
            continue
        if len(block) <= max_chars:
            spans.append(block)
            continue
        current = ""
        for sentence in re.split(r"(?<=[.!?])\s+", block):
            if current and len(current) + len(sentence) + 1 > max_chars:
                spans.append(current.strip())
                current = sentence
            else:
                current = f"{current} {sentence}".strip()
        if current:
            spans.append(current.strip())
    return spans


def main() -> int:
    ap = argparse.ArgumentParser(description="저본 텍스트를 span 코퍼스로 변환한다")
    ap.add_argument("--input", required=True, help="저본 텍스트 파일 (공유 저작물 원문)")
    ap.add_argument("--work-id", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--lang", default="en")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-chars", type=int, default=900,
                    help="한 span의 상한. MIP은 이보다 클 수 있으므로 prereq_spans로 잇는다")
    args = ap.parse_args()

    raw = Path(args.input).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    chunks = segment(raw.decode("utf-8"), args.max_chars)

    spans = {}
    previous: str | None = None
    for i, chunk in enumerate(chunks, 1):
        sid = f"{args.work_id}.{i:04d}"
        spans[sid] = {
            "work_id": args.work_id,
            "work_title": args.title,
            "locus": f"{i}번째 단락",
            "lang_src": args.lang,
            "text_src": chunk,
            "text_ko": None,                       # 인간 번역가가 채운다 (L3)
            "translator_id": None,
            "translation_status": "untranslated",
            "verified": "sourced",
            "source_sha256": digest,
            "source_file": Path(args.input).name,
            "mip_class": "standalone" if previous is None else "requires_prereq",
            "prereq_spans": [] if previous is None else [previous],
            "income_tags": [],                     # 편집자가 채운다
            "viewpoint": None,                     # π 제어에 필요 — 편집자가 채운다
            "difficulty": 2,
        }
        previous = sid

    Path(args.out).write_text(
        json.dumps({"meta": {"built_from": args.input, "sha256": digest,
                             "work_id": args.work_id, "span_count": len(spans)},
                    "spans": spans}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    print(f"{len(spans)}개 span → {args.out}  (저본 sha256={digest[:16]}…)")
    print("다음 단계: viewpoint / income_tags / text_ko 를 채워야 인용 가능해진다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
