# 필담(筆談) — PILDAM

> **AI와의 채팅으로 훌륭한 문학을 경험한다.**
> 고전 문학가·철학자를 대화 상대로 두되, **문학은 인용되고 AI는 대화한다.**

「필담(筆談)」은 말이 통하지 않는 사람들이 글로 나누던 대화를 뜻한다. 연암 박지원은 열하로 가는 길에
중국 문인들과 붓으로 대화했다. 400년 전 사람, 다른 언어를 쓰는 사람, 이미 죽은 사람과 대화하는
유일한 방법은 예나 지금이나 **쓰인 것**이다. 이 프로젝트의 이름이자 방법론이다.

---

## 이 프로젝트의 한 문장

**AI는 A+ 문학을 쓸 수 없다. 그러므로 우리는 AI에게 문학을 쓰게 하지 않는다.**
AI는 이미 존재하는 A+ 문학을 인용하고, 위치시키고, 도발하고, 독자가 계속 읽게 만드는 **대화자**다.
미학적 하중을 지는 모든 문장은 죽은 인간 저자에게 귀속된다.

이것이 [선행 논문](../paper/narrative-state-is-not-memory.ko.md)의 **모델 강등(model demotion)** 규칙
— "모델이 저작한 명제는 결코 직접 캐논에 진입하지 않는다" — 을 문학 제품의 미학적 보증으로 격상시킨 것이다.

## 문서 구성

| 문서 | 내용 |
|---|---|
| [`01-vision-and-doctrine.md`](01-vision-and-doctrine.md) | 비전, 「훌륭한 문학」과 「좋은 작가」의 조작적 정의, 미끄러움 비판의 제품적 번역, 5개 설계 법칙 |
| [`02-nams-inheritance.md`](02-nams-inheritance.md) | 선행 논문 방법론의 계승 — 3계층 매핑, 캐논 중재기 재정의, **(δ, π) 2차원 활력 프론티어**, 독자 코어 도입 |
| [`03-roster-and-rights.md`](03-roster-and-rights.md) | 1기 문우 6인 명단과 선정 논거, 한국 저작권법 분석(원문 vs 번역), 번역 코퍼스 전략 |
| [`04-architecture.md`](04-architecture.md) | 인용 우선 생성 파이프라인, 금칙 문체, 코퍼스 구축, 데이터 모델, 모델 구성 |
| [`05-metrics-and-evaluation.md`](05-metrics-and-evaluation.md) | VQR·FEL·SLP·CES·UNV 지표 체계, 실험 설계, **하중 예측과 실패 조건** |
| [`06-korea-gtm.md`](06-korea-gtm.md) | 한국 시장 진입, 세그먼트, 경쟁, 규제(AI 기본법·저작권법), 가격, 12개월 로드맵 |
| [`07-risks-and-ethics.md`](07-risks-and-ethics.md) | 위험 등록부, 반대론, 제약형 목적함수, 사후 인격적 이익 |
| [`specs/character-cards.yaml`](specs/character-cards.yaml) | 1기 문우 6인 캐릭터 카드 (페르소나 코어 명세) |
| [`specs/response-contract.md`](specs/response-contract.md) | 응답 계약 — 블록 스키마, VQR 하한, 금칙 문체, 검증 규칙 |
| [`tools/validate_response.py`](tools/validate_response.py) | 응답 계약 검증기 (실행 가능) |
| [`tools/pildam.py`](tools/pildam.py) | **대화 프로토타입 (실행 가능)** — 04장 파이프라인 ①~⑦ 전체 |
| [`tools/build_corpus.py`](tools/build_corpus.py) | 저본 텍스트 → span 코퍼스 변환기 |
| [`server/`](server/) | **런타임 생성판** — 엔진, API, 클라이언트. 제품의 기준 |
| [`app/`](app/) | 오프라인 미리보기 — 네트워크 없이 도는 정적판 |
| [`corpus/`](corpus/) | 코퍼스(`pildam-v2.json`, sourced 10 span)와 Gemini 프레임 뱅크, 검증 등급 규칙 |
| [`tools/extract_spans.py`](tools/extract_spans.py) | 저본에서 특정 대목을 span으로 추출 |
| [`tools/gen_frames.py`](tools/gen_frames.py) | 프레임 뱅크 생성 (Gemini) |

## 실제로 대화해 보기

### 서버 — 런타임 생성판 (제품의 기준)

```bash
pip install fastapi uvicorn requests
GEMINI_API_KEY=... python3 project-pildam/server/app.py    # http://127.0.0.1:8000
```

의도 목록도, 응답 뱅크도, 키워드 표도 없다. 손으로 쓰는 것은 문우 카드·코퍼스·계약 셋뿐이고
나머지는 매 턴 생성된다. 모델은 읽고 쓰고, 코드는 정책과 계약을 집행한다.
자세한 것은 [`server/README.md`](server/README.md).

### 채팅 앱 (오프라인 미리보기)

`app/index.html` — 제타식 채팅 UI. 문우를 고르고 말을 걸면 원문이 온다.
원문 카드는 말풍선이 아니고, 모델의 말은 작고 부차적이다. 화면이 곧 이 프로젝트의 논지다.

```bash
python3 project-pildam/app/build.py   # 코퍼스 + 프레임 뱅크를 단일 HTML로 묶는다
```

네트워크를 쓰지 않는다. 원문과 프레임이 전부 페이지 안에 들어가고,
δ/π 컨트롤러·검색·MIP 확장·계약 검증이 브라우저에서 그대로 돈다.
프레임 문장은 `tools/gen_frames.py`가 Gemini로 미리 만들어 둔 것이며,
모델은 여기서도 인용문 텍스트를 만들지 않는다.

### CLI

```bash
python3 project-pildam/tools/pildam.py --demo     # 스크립트 데모
python3 project-pildam/tools/pildam.py            # 대화 모드 (/state /tau <n> /work <id> /quit)
python3 project-pildam/tools/validate_response.py --self-test
```

의존성 없음, API 키 불필요. 기본 엔진 `mock`은 결정론적이며 파이프라인 전체를 실행한다 —
독서 상태 갱신, (δ, π) 컨트롤러, viewpoint 조건부 검색, MIP 확장, 계약 검증과 재생성,
그리고 실패 시 원문 단독 폴백까지.

`--engine claude`는 ⑤ 프레임 생성만 Messages API로 바꾼다. 나머지 여섯 단계는 동일하다.
모델은 여전히 **인용문 텍스트를 만들지 않는다** — span_id를 고르고 프레임 문장만 쓴다.
`ANTHROPIC_API_KEY` 또는 `ant auth login` 프로필이 필요하다.

```bash
pip install anthropic
python3 project-pildam/tools/pildam.py --engine claude --demo
```

`--min-verification sourced`(실서비스 기본값)로 실행하면 샘플 코퍼스는 아무것도 인용하지 못한다.
저본 대조를 마치지 않은 텍스트는 인용할 수 없다는 L3가 데이터 계층에서 집행되기 때문이다.

## 세 줄 요약

1. **비전** — 요약본으로 대체할 수 없는 분량의 원문을, 적확한 표현 그대로, 대화를 통해 끝까지 읽게 한다.
2. **방법** — 선행 논문의 NAMS 3계층을 계승하되, 성장하는 주체를 캐릭터에서 **독자**로 뒤집는다.
   작가는 이미 죽었고 완결됐다. 변하는 것은 읽는 사람이다.
3. **검증** — 원문 접촉량이 대화의 재미보다 30일 잔존을 더 잘 설명하지 못하면, 이 프로젝트의 전제는 틀렸다.
