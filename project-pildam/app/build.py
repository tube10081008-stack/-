#!/usr/bin/env python3
"""app/index.template.html + 코퍼스 + 프레임 뱅크 → 배포용 단일 HTML.

앱은 네트워크를 쓰지 않는다. 원문과 프레임이 전부 페이지 안에 들어간다.
프레임 뱅크는 tools/gen_frames.py가 Gemini로 미리 만들어 둔 것이며,
모델은 여전히 인용문 텍스트를 만들지 않는다 — 프레임 문장만 만든다.
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
KEEP = ("work_id", "work_title", "locus", "text_src", "text_ko",
        "prereq_spans", "viewpoint", "difficulty", "income_tags")


def main() -> None:
    corpus = json.loads((ROOT / "corpus/pildam-v2.json").read_text(encoding="utf-8"))["spans"]
    bank = json.loads((ROOT / "corpus/frames-gemini.json").read_text(encoding="utf-8"))
    slim = {k: {f: v[f] for f in KEEP} for k, v in corpus.items()}

    html = (ROOT / "app/index.template.html").read_text(encoding="utf-8")
    html = html.replace("__CORPUS__", json.dumps(slim, ensure_ascii=False))
    html = html.replace("__BANK__", json.dumps(bank, ensure_ascii=False))
    out = ROOT / "app/index.html"
    out.write_text(html, encoding="utf-8")
    print(f"{len(html)/1024:.0f} KB → {out.relative_to(ROOT)}  "
          f"(spans={len(slim)}, bank={len(bank)})")


if __name__ == "__main__":
    main()
