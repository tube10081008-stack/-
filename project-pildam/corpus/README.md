# 코퍼스

## 검증 등급 — 이것이 L3의 집행 지점이다

| 등급 | 뜻 | 인용 가능? |
|---|---|---|
| `sourced` | 확정된 저본 파일에서 `build_corpus.py`가 기계 추출. `source_sha256` 보유 | **가능. 실서비스 기본값** |
| `self_attested` | 널리 알려진 텍스트를 옮긴 것. 저본 대조 전 | 기본값에서 **거부**. `--min-verification self_attested` 로만 허용 |
| `placeholder` | 자리표시자. 실제 원문이 아님 | 언제나 거부 |

렌더러는 등급 미달 span을 아예 후보에서 제외하고, 그 사실을 화면에 표시한다.
**요약으로 대체하지 않는다** — 인용할 수 없으면 인용하지 않고, 그렇다고 지어내지도 않는다(L1·L2).

## 현재 샘플 코퍼스의 상태

`sample.json`은 데모용이며 다음 한계를 그대로 노출한다.

- 셰익스피어 3개 span은 `self_attested`다. 저본 대조를 하지 않았으므로 실서비스 기준으로는 **인용 불가**다.
- 오스틴 2개 span은 `placeholder`다. 실제 원문이 아니며, 데모에서 인용이 거부되는 모습을 보여 준다.
- 한국어 번역은 전부 `sample_pending_human` — 샘플이며 인간 문학번역가의 확정을 기다린다(L3).
- 셰익스피어 span은 1~2행짜리라 **MIP 미만**이다. 그 결과 정의감 호출이 VQR 0.75를 만족하지 못하고
  폴백된다. 이것은 버그가 아니라 계약이 옳게 작동하는 것이다 — 관점을 한 줄로 요약하면 허수아비가 된다.

## 실제 코퍼스 만들기

1. **저본을 확보한다.** 공유 저작물 원문(Project Gutenberg, Wikisource, 국립중앙도서관 등).
   판본·편집·주석에 별도 권리가 붙을 수 있으므로 03장 3.4.6절의 확인 목록을 먼저 통과할 것.
2. **분절한다.**
   ```bash
   python3 tools/build_corpus.py --input hamlet.txt \
       --work-id shakespeare.hamlet --title 햄릿 --lang en --out corpus/hamlet.json
   ```
   저본 파일의 SHA-256이 모든 span에 기록되어, 어떤 파일에서 나온 텍스트인지 감사할 수 있다.
3. **편집자가 메타데이터를 채운다.** `viewpoint`(π 제어에 필수), `income_tags`, `difficulty`,
   `mip_class`/`prereq_spans`, `wildness_note`.
4. **번역가가 `text_ko`를 확정한다.** 기계 초벌은 허용되나 최종 문장은 사람이 정한다.
   `translator_id`와 번역 결정 이력을 남긴다(L3, 「적확성 대조」의 소재이기도 하다).

`viewpoint`가 비어 있으면 π 제어가 작동하지 않는다. 이 필드가 이 시스템에서
관점 거리를 물리적으로 가능하게 만드는 유일한 근거다.
