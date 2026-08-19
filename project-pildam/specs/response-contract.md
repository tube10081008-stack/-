# 응답 계약 (Response Contract)

필담의 모든 턴은 이 계약을 통과해야 렌더링된다. 통과하지 못하면 재생성하고,
두 번 실패하면 **인용 단독 폴백**으로 응답한다(04장 4.2절).

## 1. 원칙

> **모델은 인용문의 텍스트를 출력하지 않는다. `span_id`만 출력한다.**

`quote` 블록에 `text` 필드를 담아 보내는 모델 출력은 계약 위반이며 즉시 기각된다.
텍스트는 서버가 코퍼스에서 materialize한다. 이것이 L1을 확률이 아니라 구조로 보장하는 지점이다.

## 2. 턴 스키마

```json
{
  "turn_id": "t_00412",
  "session_type": "reading",         // reading | dialogue
  "writer_id": "austen",
  "tau": 27,                          // 관계 연령 (세션 수)
  "delta": 0.42,                      // 기억 의존도 (계층 III)
  "pi": 0.71,                         // 관점 거리 (계층 III)
  "blocks": [
    {"type": "frame",    "provenance": "model", "modality": "hypothesis",
     "text": "당신은 어제 다아시를 오만하다고 판정했습니다. 그 판정을 잠시 보류해 달라는 것이 아닙니다."},
    {"type": "appeal",   "provenance": "model", "modality": "hypothesis",
     "text": "당신의 감정은 이 편지를 탐탁지 않게 여길 것입니다. 나는 당신의 정의감에 요구합니다."},
    {"type": "quote",    "provenance": "source", "modality": "canon",
     "span_id": "austen.pp.v2.c12.s001"},
    {"type": "quote",    "provenance": "source", "modality": "canon",
     "span_id": "austen.pp.v2.c12.s002"},
    {"type": "contrast", "provenance": "model", "modality": "hypothesis",
     "span_id": "austen.pp.v2.c12.s001",
     "paraphrase": "다아시가 자기 행동을 해명하는 대목."}
  ]
}
```

## 3. 블록 유형

| type | provenance | modality | 규칙 |
|---|---|---|---|
| `quote` | `source` | `canon` | `span_id`만. `text` 금지. 서버가 materialize |
| `frame` | `model` | `hypothesis` | 모델 저작. 금칙 문체 금지. 예산 제한 |
| `appeal` | `model` | `hypothesis` | 정의감 호출. τ·안전 플래그 조건 충족 시에만 |
| `contrast` | `model` | `hypothesis` | 적확성 대조. 모델의 패러프레이즈를 원문 옆에 전시 |
| `reader` | `reader` | `canon`(승격 시) | 독자 해석의 인용. 승격 규칙은 02장 2.5절 |

**불변식**: `provenance == "model"` 인 블록은 `modality == "canon"` 을 가질 수 없다.
이 한 줄이 논문의 모델 강등이자 필담의 L1이다.

## 4. 정량 제약

| 제약 | 값 | 근거 |
|---|---|---|
| VQR 하한 (reading) | **0.60** | L2 — 독서 세션은 원문이 다수여야 한다 |
| VQR 하한 (dialogue) | **0.35** | 대화 세션도 바닥은 있다 |
| VQR 하한 (appeal 포함 턴) | **0.75** | 관점을 요약하면 허수아비가 된다 (04장 4.5절) |
| 프레임 예산 | 턴당 모델 저작 ≤ **400자**, 그리고 reading 세션에서 ≤ 0.8 × 인용 문자수 | 미끄러움의 총량 통제 |
| MIP | `mip_class = requires_prereq` 인 span은 `prereq_spans` 동반 필수 | L2 |
| appeal τ 임계 | 기본 **τ ≥ 10** (설정 가능) | H1′ — 높은 π는 벌어야 한다 |

VQR = 인용 문자수 / (인용 문자수 + 모델 저작 문자수). `contrast.paraphrase`는 모델 저작에 산입된다.

## 5. 금칙 문체

| 분류 | 차단 대상 |
|---|---|
| `mirroring` | 감정 미러링 ("그 마음 이해해요", "슬프시겠어요") |
| `evaluative` | 작품 평가 형용사 ("위대한 작품", "아름다운 문장") |
| `summarizing` | 요약 접속사 ("요컨대", "정리하자면", "한마디로") |
| `fabricated_interiority` | 출처 없는 1인칭 내면 서술 |
| `harmless_balance` | 무해한 균형 ("물론 반대 의견도 있습니다만") — π를 스스로 0으로 되돌린다 |
| `anachronism` | 문우 몰년 이후의 개념·사물 |

SLP = 금칙에 걸린 모델 저작 문장 수 / 전체 모델 저작 문장 수.

## 6. 검증기

[`../tools/validate_response.py`](../tools/validate_response.py) 가 위 규칙 전부를 집행한다.
CI에서 프롬프트·모델 변경마다 회귀 실행한다.

```bash
python3 project-pildam/tools/validate_response.py --self-test
python3 project-pildam/tools/validate_response.py --corpus corpus.json --turn turn.json
```
