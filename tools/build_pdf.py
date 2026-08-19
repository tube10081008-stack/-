#!/usr/bin/env python3
import re, sys, markdown
from weasyprint import HTML, CSS

SRC = "/home/user/-/paper/narrative-state-is-not-memory.ko.md"
OUT = "/home/user/-/paper/서사상태는_기억이_아니다.pdf"

raw = open(SRC, encoding="utf-8").read()

# Split off the cover block (title + subtitle + version) from the body.
lines = raw.split("\n")
title = lines[0].lstrip("# ").strip()
subtitle = lines[1].lstrip("# ").strip()
version = lines[3].strip()
body_md = "\n".join(lines[4:]).lstrip("\n")
body_md = body_md.replace("---\n", "", 1).lstrip("\n")   # drop the first hr after the cover

md = markdown.Markdown(extensions=["tables", "attr_list", "sane_lists", "toc", "md_in_html"],
                       extension_configs={"toc": {"toc_depth": "2-3"}})
body_html = md.convert(body_md)
body_html = re.sub(
    r'(<p><strong>표\s*\d+\..*?</strong></p>)\s*(<table>.*?</table>)',
    r'<div class="tablewrap">\1\2</div>', body_html, flags=re.S)
toc_html = md.toc

CSS_TEXT = r"""
@page {
  size: A4;
  margin: 24mm 20mm 22mm 20mm;
  @top-center {
    content: "서사 상태는 기억이 아니다 — 페르소나 스토리텔링을 위한 3축 설계 공간과 NAMS";
    font-family: "Noto Sans CJK KR", "NanumBarunGothic", sans-serif;
    font-size: 7.5pt; color: #8a8a8a; padding-bottom: 3mm;
  }
  @bottom-center {
    content: counter(page);
    font-family: "Noto Sans CJK KR", sans-serif;
    font-size: 8.5pt; color: #666; padding-top: 3mm;
  }
}
@page :first { @top-center { content: none; } @bottom-center { content: none; } }

html { font-size: 10.5pt; }
body {
  font-family: "Noto Serif CJK KR", "NanumMyeongjo", "Noto Serif", serif;
  line-height: 1.78; color: #14161a; text-align: justify;
  word-break: keep-all; overflow-wrap: break-word; hyphens: none;
}

/* ---- cover ---- */
.cover { page-break-after: always; padding-top: 34mm; }
.cover .kicker {
  font-family: "Noto Sans CJK KR", sans-serif; font-size: 8.5pt; letter-spacing: .22em;
  color: #7a6a4f; text-transform: uppercase; margin-bottom: 12mm;
}
.cover h1 {
  font-family: "Noto Sans CJK KR", "NanumBarunGothic", sans-serif;
  font-size: 26pt; line-height: 1.32; font-weight: 700; margin: 0 0 6mm 0;
  letter-spacing: -.01em; border: 0; padding: 0; text-align: left;
}
.cover h2 {
  font-family: "Noto Sans CJK KR", sans-serif; font-size: 13pt; font-weight: 400;
  line-height: 1.55; color: #4a4f57; margin: 0 0 16mm 0; border: 0; padding: 0;
}
.cover .rule { border-top: 2.5pt solid #14161a; width: 46mm; margin-bottom: 8mm; }
.cover .meta {
  font-family: "Noto Sans CJK KR", sans-serif; font-size: 9.5pt; color: #5c626b; line-height: 1.9;
}
.cover .note {
  margin-top: 26mm; padding: 5mm 6mm; background: #f6f4ef; border-left: 2.5pt solid #b9a87e;
  font-family: "Noto Sans CJK KR", sans-serif; font-size: 8.5pt; color: #4a4f57; line-height: 1.7;
  text-align: left;
}

/* ---- table of contents ---- */
.toc { page-break-after: always; }
.toc h2 {
  font-family: "Noto Sans CJK KR", sans-serif; font-size: 12pt; letter-spacing: .1em;
  border: 0; border-bottom: 1.5pt solid #14161a; padding-bottom: 3mm; margin-bottom: 5mm;
}
.toc ul { list-style: none; padding-left: 0; margin: 0; }
.toc ul ul { padding-left: 7mm; }
.toc li { margin: 0.9mm 0; font-family: "Noto Sans CJK KR", sans-serif; font-size: 9.5pt; }
.toc ul ul li { font-size: 8.6pt; color: #5c626b; }
.toc a { color: inherit; text-decoration: none; }

/* ---- headings ---- */
h1, h2, h3, h4 {
  font-family: "Noto Sans CJK KR", "NanumBarunGothic", sans-serif;
  text-align: left; word-break: keep-all; page-break-after: avoid;
}
h2 {
  font-size: 14pt; font-weight: 700; margin: 11mm 0 4mm; padding-bottom: 2.5mm;
  border-bottom: 1.2pt solid #d6d2c8; letter-spacing: -.01em;
}
h3 { font-size: 11.2pt; font-weight: 700; margin: 7mm 0 2.5mm; color: #1f2937; }
h4 { font-size: 10pt; font-weight: 700; margin: 5mm 0 2mm; }

p { margin: 0 0 3.2mm; orphans: 2; widows: 2; }
strong { font-weight: 700; }
em { font-style: italic; }
a { color: #14161a; text-decoration: none; }
hr { border: 0; border-top: 1pt solid #ddd9d0; margin: 8mm 0; }

/* ---- equation / callout blockquotes ---- */
blockquote {
  margin: 4mm 0; padding: 3.5mm 6mm; background: #f7f6f2;
  border-left: 2.5pt solid #b9a87e; text-align: left;
}
blockquote p { margin: 0 0 1.5mm; }
blockquote p:last-child { margin-bottom: 0; }

/* ---- lists ---- */
ul, ol { margin: 0 0 3.5mm; padding-left: 6mm; }
li { margin: 1.2mm 0; }

/* ---- tables ---- */
table {
  width: 100%; border-collapse: collapse; margin: 4mm 0 5mm;
  font-family: "Noto Sans CJK KR", "NanumBarunGothic", sans-serif;
  font-size: 8.2pt; line-height: 1.55; text-align: left;
  page-break-inside: auto;
}
thead { display: table-header-group; }
.tablewrap { page-break-inside: avoid; margin: 4mm 0 5mm; }
.tablewrap > p { margin-bottom: 1.5mm; font-family: "Noto Sans CJK KR", sans-serif; font-size: 9pt; }
.tablewrap > table { margin: 0; }
tr { page-break-inside: avoid; }
th {
  background: #14161a; color: #fff; font-weight: 600; padding: 2mm 2.2mm;
  border: 0; text-align: left; vertical-align: bottom;
}
td { padding: 2mm 2.2mm; border-bottom: .5pt solid #e2ded6; vertical-align: top; word-break: keep-all; }
tbody tr:nth-child(even) td { background: #faf9f6; }
table strong { font-weight: 700; }

code {
  font-family: "Noto Sans Mono CJK KR", "DejaVu Sans Mono", monospace;
  font-size: 8.6pt; background: #f2f0eb; padding: .3mm 1mm; border-radius: 1.5pt;
}

/* references */
h2#참고문헌 + ol li { font-size: 9pt; line-height: 1.65; margin: 1.6mm 0; text-align: left; }
"""

HTML_DOC = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><title>{title}</title></head>
<body>
<section class="cover">
  <div class="kicker">Working Paper · Persona LLM Research</div>
  <div class="rule"></div>
  <h1>{title}</h1>
  <h2>{subtitle}</h2>
  <div class="meta">
    작업 논문(Working Paper) · SCI 투고 서식<br>
    버전 1.0 — 2026년 8월<br>
    페르소나 LLM 시장 분석 · 기술 계보 조사 · 최신 연구 비교에 기반함
  </div>
  <div class="note">
    <strong>근거 자료 고지.</strong> 본 논문에 인용된 참여도 수치는 기업 블로그·언론 보도·서드파티 앱 분석 등
    2차 출처이며 독립 감사를 거치지 않았습니다. 파생 추정치는 "추정"으로 표기했습니다.
    정성적 순서(페르소나 플랫폼이 범용 어시스턴트와 구별되는 참여도 영역을 점유한다)는 견고하나,
    개별 점추정치를 효과크기 산정에 사용해서는 안 됩니다.
  </div>
</section>

<section class="toc">
  <h2>목차</h2>
  {toc_html}
</section>

<main>
{body_html}
</main>
</body></html>"""

HTML(string=HTML_DOC, base_url="/home/user/-").write_pdf(OUT, stylesheets=[CSS(string=CSS_TEXT)])
print("wrote", OUT)
