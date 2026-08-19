#!/usr/bin/env python3
"""문우별 응대(chrome) 라인 생성.

인사·자기소개·"너 AI야?"·딴소리에 대한 응답은 원문을 인용하지 않는다.
문학적 소득을 주장하지 않으므로 인용이 필요 없고, 대신 짧아야 한다.
이 라인들은 전부 모델 저작이며 캐논에 진입하지 않는다(L1).
"""
import json, os, pathlib, sys, time, requests

KEY = os.environ["GEMINI_API_KEY"]
URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-pro-preview:generateContent"
OUT = pathlib.Path(__file__).resolve().parent.parent / "corpus" / "chrome-gemini.json"

WRITERS = {
    "shakespeare": dict(
        name="윌리엄 셰익스피어", died=1616,
        works="소네트, 햄릿",
        facts="플롯을 홀린셰드 연대기와 플루타르코스와 이탈리아 노벨라에서 거리낌 없이 가져다 썼다. "
              "작품 편차가 크고 공동 집필작이 있다. 극장의 지분을 가진 흥행업자이기도 했다."),
    "austen": dict(
        name="제인 오스틴", died=1817,
        works="오만과 편견",
        facts="생전 익명으로 출판했다('By a Lady'). 무대가 좁고 소재가 반복된다고 스스로 말했다 — "
              "조카에게 보낸 편지에서 자기 작업을 '두 인치 상아 조각'에 비유했다."),
}

SYSTEM = """너는 문학 서비스 「필담」의 문우 에이전트다. 고전 작가를 대신해 독자와 대화한다.

너의 위치를 정확히 알아라. 너는 그 작가가 아니다. 너는 그 작가가 쓴 것을 독자에게 건네는 대화자다.
이 사실을 숨기지 않는다. 그러나 굽신거리지도 않는다.

절대 규칙:
- 원문을 인용하거나 지어내지 않는다.
- 출처 없는 1인칭 내면 고백 금지("저는 그때 외로웠습니다"). 사실과 태도만 말한다.
- 금칙: 감정 미러링, 작품 평가 형용사, 요약 접속사, 무해한 균형, 이모지, 느낌표 남발,
  "무엇을 도와드릴까요" 같은 비서 어투, "함께 여행을 떠나볼까요" 같은 들뜬 권유.
- 문체: 건조하고 단정적이다. 존댓말. 한 문장에서 두 문장. 짧을수록 좋다."""

SCHEMA = {"type": "OBJECT", "properties": {
    "greeting": {"type": "ARRAY", "items": {"type": "STRING"}},
    "identity": {"type": "ARRAY", "items": {"type": "STRING"}},
    "ai": {"type": "ARRAY", "items": {"type": "STRING"}},
    "offtopic": {"type": "ARRAY", "items": {"type": "STRING"}},
    "invite": {"type": "ARRAY", "items": {"type": "STRING"}},
}, "required": ["greeting", "identity", "ai", "offtopic", "invite"]}


def gen(wid, w):
    ask = f"""문우: {w['name']} (몰년 {w['died']}). 함께 읽을 것: {w['works']}.
문서화된 사실과 결점: {w['facts']}

아래 항목마다 서로 다른 각도로 3개씩 써라. 각 문장 60자 이내.

- greeting: 독자가 "안녕", "안녕하세요" 하고 인사했을 때. 인사를 받되 잡담으로 흐르지 않는다.
- identity: 독자가 "넌 누구야"라고 물었을 때. 누구의 글을 건네는 자리인지 말하고,
  위의 결점 중 하나를 스스로 먼저 꺼낸다. 미화하지 않는다.
- ai: 독자가 "너 AI야?", "진짜 {w['name']}야?"라고 물었을 때.
  거짓말하지 않는다. 나는 그 사람이 아니고, 여기서 진짜인 것은 인용되는 문장뿐이라고 분명히 말한다.
- offtopic: 독자가 날씨·심심함·잡담처럼 읽기와 무관한 말을 걸었을 때.
  면박 주지 말고, 짧게 받고 읽기로 되돌린다.
- invite: 위 응답 뒤에 붙일 한 줄. 첫 대목을 보자고 청한다. 들뜨지 않게."""

    r = requests.post(URL, params={"key": KEY}, timeout=180, json={
        "systemInstruction": {"parts": [{"text": SYSTEM}]},
        "contents": [{"role": "user", "parts": [{"text": ask}]}],
        "generationConfig": {"responseMimeType": "application/json", "responseSchema": SCHEMA,
                             "temperature": 1.0, "maxOutputTokens": 4096}})
    r.raise_for_status()
    cand = r.json()["candidates"][0]
    txt = "".join(p.get("text", "") for p in (cand.get("content", {}).get("parts") or []))
    if not txt.strip():
        raise RuntimeError(f"empty ({cand.get('finishReason')})")
    return json.loads(txt)


def main() -> int:
    bank = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    for wid, w in WRITERS.items():
        if wid in bank:
            print(f"  skip {wid}"); continue
        for attempt in range(3):
            try:
                bank[wid] = gen(wid, w)
                OUT.write_text(json.dumps(bank, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"  ok  {wid}"); break
            except Exception as e:
                print(f"  retry {wid} ({attempt+1}): {str(e)[:80]}"); time.sleep(3)
        else:
            print(f"  FAIL {wid}"); return 1
    print(f"{len(bank)} writers → {OUT.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
