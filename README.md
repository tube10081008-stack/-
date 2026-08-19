# 페르소나 LLM 리서치 → SCI급 논문

페르소나 LLM(제타 등) 상위 프로젝트 선정 → 핵심 개발자·기술 계보 정리 → 최신 화제 논문 비교 →
페르소나 스토리텔링의 향후 방향에 관한 논문 작성까지의 전체 산출물.

## 구성

| 파일 | 내용 |
|---|---|
| [`research/01-selection-and-evidence.md`](research/01-selection-and-evidence.md) | **1단계.** "많은 고객을 오래 점유"라는 기준(규모 × 체류 × 지속)으로 zeta / Character.AI / Talkie·Xingye 선정, 근거 데이터와 탈락 후보 사유 |
| [`research/02-core-developers-and-technology.md`](research/02-core-developers-and-technology.md) | **2단계.** 각 프로젝트 핵심 개발자, 그들이 저술한 연구 계보, 제품에 차용한 기술 스택 |
| [`research/03-hyped-papers-comparison.md`](research/03-hyped-papers-comparison.md) | **3단계.** 현시점 최고 화제 논문 3편(HOPE/Nested Learning, ALMA, SteeM) 개요와 정면 비교, 네 가지 구조적 공백 |
| [`paper/narrative-state-is-not-memory.md`](paper/narrative-state-is-not-memory.md) | **4단계.** 본 논문 (영문) — *Narrative State Is Not Memory: A Three-Axis Design Space and the NAMS Architecture for Persona Storytelling Systems* |
| [`paper/narrative-state-is-not-memory.ko.md`](paper/narrative-state-is-not-memory.ko.md) | 본 논문 **국문판** — 「서사 상태는 기억이 아니다: 페르소나 스토리텔링 시스템을 위한 3축 설계 공간과 NAMS 아키텍처」 |
| [`paper/서사상태는_기억이_아니다.pdf`](paper/서사상태는_기억이_아니다.pdf) | 국문판 조판 PDF (A4 19쪽, 표지·목차·러닝헤드 포함) |
| [`tools/build_pdf.py`](tools/build_pdf.py) | 국문 마크다운 → PDF 조판 스크립트 (WeasyPrint) |
| [`project-pildam/`](project-pildam/) | **5단계.** 논문 방법론을 적용한 실제 프로젝트 — 「필담(筆談)」, 고전 문학가·철학자를 문우로 두는 한국 시장 문학 경험 서비스 |

## 핵심 주장 한 줄 요약

산업(저비용 서빙 / 초장문 컨텍스트 / 온라인 정렬)도 학계(HOPE / ALMA / SteeM)도 모두 **회상 충실도**를
최적화하고 있으나, 장기 페르소나 서사의 실제 실패는 **앵커링**(완벽한 기억 → 예측 가능성 → 이탈)이다.
다음 진보는 더 많이 기억하는 것이 아니라 **기억의 권한(δ)을 서사 상태에 따라 조절하는 것**에서 온다.

## 파생 프로젝트 — 필담(筆談)

논문의 NAMS 방법론을 그대로 계승해 설계한 제품이 [`project-pildam/`](project-pildam/)에 있다.
셰익스피어·톨스토이·단테·소크라테스·오스틴·박지원을 문우(文友)로 두되, **문학은 인용되고 AI는 대화한다.**
논문의 「모델 강등」 규칙이 여기서는 미학적 보증으로 격상된다 — 미학적 하중을 지는 모든 문장은
죽은 인간 저자에게 귀속되며, 모델은 인용문의 텍스트를 아예 출력하지 않는다(span 좌표만 출력).

## 데이터 신뢰도 고지

참여도 수치는 기업 블로그·보도·서드파티 앱 분석의 2차 출처이며 독립 감사를 거치지 않았다.
파생 추정치는 `[추정]`/`(est.)`로 표기했다. 순서(페르소나 플랫폼이 범용 어시스턴트와 다른 참여도
영역에 있다)는 견고하나, 개별 수치를 효과크기 산정에 사용해서는 안 된다.
