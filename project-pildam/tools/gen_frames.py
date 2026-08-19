import json, os, sys, time, requests

CORPUS = json.load(open("/home/user/-/project-pildam/corpus/pildam-v2.json", encoding="utf-8"))["spans"]
KEY = os.environ["GEMINI_API_KEY"]
URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-pro-preview:generateContent"

SYSTEM = """너는 문학 서비스 「필담」의 문우 에이전트다. 고전 작가를 대신해 독자와 대화한다.

절대 규칙:
- 너는 문학을 쓰지 않는다. 원문을 인용하거나 옮겨 적지 않는다. 원문은 시스템이 따로 보여 준다.
- 너는 원문 옆에 놓일 짧은 '프레임' 문장만 쓴다. 독자가 읽어야 할 것은 네 말이 아니라 원문이다.
- 금칙: 감정 미러링("그 마음 이해해요"), 작품 평가 형용사("아름다운 문장", "위대한 작품"),
  요약 접속사("요컨대", "정리하자면", "한마디로"), 무해한 균형("물론 반대 의견도 있습니다만"),
  출처 없는 1인칭 내면 고백, 이모지, 느낌표 남발.
- 문체: 건조하고 단정적이다. 존댓말. 한 문장 또는 두 문장. 설명하지 말고 겨누어라."""

SCHEMA = {"type": "OBJECT", "properties": {
    "continue": {"type": "ARRAY", "items": {"type": "STRING"}},
    "question": {"type": "ARRAY", "items": {"type": "STRING"}},
    "verdict":  {"type": "ARRAY", "items": {"type": "STRING"}},
    "agree":    {"type": "ARRAY", "items": {"type": "STRING"}},
    "summary_request": {"type": "ARRAY", "items": {"type": "STRING"}},
    "highlight": {"type": "ARRAY", "items": {"type": "STRING"}},
    "appeal": {"type": "STRING"},
    "paraphrase": {"type": "STRING"},
    "probe": {"type": "STRING"},
}, "required": ["continue","question","verdict","agree","summary_request","highlight",
                "appeal","paraphrase","probe"]}

def gen(sid, span):
    budget = max(30, int(0.45 * len(span["text_ko"])))
    ask = f"""아래 원문 대목에 붙일 프레임 문장들을 만들어라.

작품: {span['work_title']} · {span['locus']}
시점: {span['viewpoint']}
감정 소득 태그: {', '.join(span['income_tags'])}
야생성 메모: {span.get('wildness_note','')}
원문(한국어 번역, 참고용 — 절대 인용하거나 옮기지 말 것):
{span['text_ko']}

각 항목마다 서로 다른 각도의 프레임을 3개씩 써라. 각 프레임은 {budget}자 이내.
- continue: 독자가 그냥 계속 읽을 때
- question: 독자가 질문했을 때 (답을 주지 말고 이 대목을 겨누어라)
- verdict: 독자가 인물이나 작가에 대해 확신에 찬 도덕적 판정을 내렸을 때 (승인하지 말 것)
- agree: 독자가 동의만 반복할 때 (승인 루프를 깨라)
- summary_request: 독자가 요약을 요구할 때 (요약해 주지 말 것. 요약이 무엇을 잃는지 겨누어라)
- highlight: 독자가 이 구절을 저장했을 때

그리고:
- appeal: 관점 거리가 최대일 때 쓰는 '정의감 호출' 한 문장. 감정이 아니라 정의감에 요구하는 어법.
  다아시의 편지가 그 원형이다. {budget}자 이내.
- paraphrase: 이 대목을 일부러 '미끄럽게' 다시 쓴 문장. 매끄럽고 무난하고 손에 잡히지 않게.
  독자에게 원문과 나란히 보여 주고 무엇이 사라졌는지 묻기 위한 대조용이다.
- probe: 독자에게 던질 짧은 질문 하나. 판단을 요구하되 정답이 없는 것."""

    r = requests.post(URL, params={"key": KEY}, timeout=180, json={
        "systemInstruction": {"parts": [{"text": SYSTEM}]},
        "contents": [{"role": "user", "parts": [{"text": ask}]}],
        "generationConfig": {"responseMimeType": "application/json",
                             "responseSchema": SCHEMA, "temperature": 1.0,
                             "maxOutputTokens": 8192}})
    r.raise_for_status()
    d = r.json()["candidates"][0]
    parts = d.get("content", {}).get("parts") or []
    txt = "".join(p.get("text", "") for p in parts)
    if not txt.strip():
        raise RuntimeError(f"{sid}: empty ({d.get('finishReason')})")
    return json.loads(txt)

import pathlib
OUT = pathlib.Path("/home/user/-/project-pildam/corpus/frames-gemini.json")
bank = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
for sid, span in CORPUS.items():
    if sid in bank:
        print(f"  skip {sid}"); continue
    for attempt in range(3):
        try:
            bank[sid] = gen(sid, span)
            print(f"  ok  {sid}  frames={sum(len(v) for k,v in bank[sid].items() if isinstance(v,list))}")
            OUT.write_text(json.dumps(bank, ensure_ascii=False, indent=2), encoding="utf-8")
            break
        except Exception as e:
            print(f"  retry {sid} ({attempt+1}): {str(e)[:90]}")
            time.sleep(3)
    else:
        print(f"  FAIL {sid}"); sys.exit(1)

OUT.write_text(json.dumps(bank, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n{len(bank)} spans → frames-gemini.json")
