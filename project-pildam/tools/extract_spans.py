import hashlib, json, pathlib
S = pathlib.Path("/tmp/claude-0/-home-user--/abd53012-c7b5-5a25-8f74-a0b0261d0a71/scratchpad")

def sha(p): return hashlib.sha256((S/p).read_bytes()).hexdigest()
def lines(p, a, b): return "\n".join(l.rstrip() for l in (S/p).read_text(encoding="utf-8", errors="replace").split("\n")[a-1:b]).strip()
def dedent(t): return "\n".join(l.strip() for l in t.split("\n") if l.strip())
def para(p, a, b):
    return " ".join(l.strip() for l in (S/p).read_text(encoding="utf-8", errors="replace").split("\n")[a-1:b] if l.strip())

SH, PP = "shakespeare.txt", "Pride-and-Prejudice_1342.txt"
sh_sha, pp_sha = sha(SH), sha(PP)

spans = {}
def add(sid, **kw): spans[sid] = kw

# ── 셰익스피어 · 소네트 18 ────────────────────────────────
S18 = [(482,485), (486,489), (490,493), (494,495)]
S18_KO = [
"그대를 여름날에 견주어 볼까요?\n그대가 더 사랑스럽고 더 온화합니다.\n거친 바람이 오월의 어여쁜 꽃봉오리를 흔들고,\n여름이 빌린 기한은 너무도 짧습니다.",
"때로 하늘의 눈이 너무 뜨겁게 타오르고,\n자주 그 금빛 얼굴은 흐려집니다.\n아름다운 것은 모두 언젠가 아름다움에서 기울어집니다,\n우연으로, 혹은 자연이 바꾸어 놓는 행로에 다듬어지지 못한 채.",
"그러나 그대의 영원한 여름은 시들지 않고,\n그대가 지닌 그 아름다움을 잃지도 않을 것이며,\n죽음도 그대가 제 그늘을 헤맨다 뽐내지 못할 것입니다,\n그대가 영원한 시행 속에서 시간을 향해 자라날 때에는.",
"사람이 숨 쉬고 눈이 볼 수 있는 한,\n이것이 살아 있고, 이것이 그대에게 생명을 줍니다.",
]
S18_META = [
 (["덧없음","찬미","비교의 실패"], "질문으로 열어 놓고 곧바로 그 비유가 모자란다고 스스로 취소한다."),
 (["쇠퇴","우연","자연"], "찬미하겠다면서 네 행을 통째로 시드는 것들에 쓴다."),
 (["영속","죽음에의 반박"], "죽음을 향해 뽐내지 말라고 직접 말을 건다."),
 (["영속","자기과시","시의 효용"], "연인을 찬미하던 시가 마지막 두 행에서 실은 자기 시를 자랑한다."),
]
prev = None
for i, ((a, b), ko, (tags, wild)) in enumerate(zip(S18, S18_KO, S18_META), 1):
    sid = f"sonnet18.{i:02d}"
    add(sid, work_id="shakespeare.sonnet18", writer_id="shakespeare", work_title="소네트 18",
        locus=f"{(i-1)*4+1}–{min(i*4,14)}행" if i < 4 else "13–14행 (결구)",
        lang_src="en", text_src=dedent(lines(SH, a, b)), text_ko=ko,
        translator_id="pildam.sample", translation_status="sample_pending_human",
        verified="sourced", source_sha256=sh_sha, source_file=SH,
        mip_class="standalone" if prev is None else "requires_prereq",
        prereq_spans=[] if prev is None else [prev],
        income_tags=tags, viewpoint="화자", difficulty=2 + (i > 2), wildness_note=wild)
    prev = sid

# ── 셰익스피어 · 햄릿 3막 1장 ────────────────────────────
HAM = [(25797,25801), (25801,25805), (25805,25810), (25810,25812)]
HAM_KO = [
"있음이냐 없음이냐, 그것이 문제로다.\n어느 쪽이 정신에 더 고귀한가 —\n난폭한 운명이 쏘아 대는 돌팔매와 화살을 견디는 것인가,\n아니면 고난의 바다에 맞서 무기를 들고,\n맞섬으로써 그것들을 끝내는 것인가.",
"죽는 것 — 잠드는 것 —\n그뿐. 그리고 잠으로써 끝낸다고 말할 수 있다면,\n가슴앓이와, 살덩이가 물려받은\n천 가지 타고난 충격들을. 그것은\n간절히 바랄 만한 완성이다.",
"죽는 것 — 잠드는 것.\n잠드는 것 — 어쩌면 꿈꾸는 것. 아, 거기에 걸림돌이 있다.\n죽음의 그 잠 속에서 무슨 꿈이 찾아올지,\n이 육신의 굴레를 벗어던졌을 때,\n그것이 우리를 멈춰 세운다.",
"바로 그 망설임이\n이토록 긴 삶을 재앙으로 만든다.\n누가 시대의 채찍질과 멸시를 견디겠는가,\n압제자의 횡포를, 오만한 자의 모욕을,",
]
HAM_META = [
 (["결정 불능","죽음","행위의 마비"], "가장 유명한 대사가 실은 아무것도 결정하지 못하는 사람의 말이다."),
 (["죽음","안식에의 유혹"], "죽음을 잠이라 부르며 스스로를 달래다가 말이 끊긴다."),
 (["공포","미지","망설임"], "죽지 못하는 이유가 용기가 아니라 무지라고 실토한다."),
 (["시스템 비판","모욕","견딤"], "개인의 우울에서 시작한 독백이 압제와 제도 이야기로 번진다."),
]
prev = None
for i, ((a, b), ko, (tags, wild)) in enumerate(zip(HAM, HAM_KO, HAM_META), 1):
    sid = f"hamlet31.{i:02d}"
    add(sid, work_id="shakespeare.hamlet", writer_id="shakespeare", work_title="햄릿",
        locus=f"3막 1장 ({i}/4)", lang_src="en",
        text_src=dedent(lines(SH, a, b)).replace("Ham. ", ""), text_ko=ko,
        translator_id="pildam.sample", translation_status="sample_pending_human",
        verified="sourced", source_sha256=sh_sha, source_file=SH,
        mip_class="standalone" if prev is None else "requires_prereq",
        prereq_spans=[] if prev is None else [prev],
        income_tags=tags, viewpoint="햄릿", difficulty=3, wildness_note=wild)
    prev = sid

# ── 오스틴 · 오만과 편견 · 다아시의 편지 ──────────────────
add("pp.letter.01", work_id="austen.pp", writer_id="austen", work_title="오만과 편견",
    locus="제2권 12장 · 다아시의 편지 첫머리", lang_src="en",
    text_src=para(PP, 6622, 6631), verified="sourced", source_sha256=pp_sha, source_file=PP,
    text_ko="놀라지 마십시오, 부인. 이 편지가 어젯밤 당신에게 그토록 역겨웠던 그 감정의 되풀이나 "
            "그 청혼의 재개를 담고 있지 않을까 하는 염려로는. 저는 당신을 아프게 하거나 저 자신을 "
            "낮추려는 의도 없이 씁니다. 둘 모두의 행복을 위해 하루빨리 잊는 편이 나은 바람들에 "
            "매달리지 않겠습니다. 이 편지를 쓰고 또 읽게 하는 수고는 마땅히 면할 수 있었을 것입니다, "
            "제 인격이 그것을 쓰고 읽히기를 요구하지 않았더라면. 그러니 당신의 주의를 요구하는 이 "
            "무례를 용서하십시오. 당신의 감정은, 압니다, 그것을 마지못해 내어 줄 것입니다. "
            "그러나 저는 당신의 정의감에 그것을 요구합니다.",
    translator_id="pildam.sample", translation_status="sample_pending_human",
    mip_class="standalone", prereq_spans=[],
    income_tags=["정의감","판단의 철회","오해"], viewpoint="다아시", difficulty=3,
    wildness_note="사과하지 않는다. 감정을 인정하면서도 감정에 호소하기를 거부한다.")

add("pp.letter.02", work_id="austen.pp", writer_id="austen", work_title="오만과 편견",
    locus="제2권 12장 · 두 가지 죄목", lang_src="en",
    text_src=para(PP, 6633, 6638), verified="sourced", source_sha256=pp_sha, source_file=PP,
    text_ko="성격이 매우 다르고 결코 경중이 같지 않은 두 가지 잘못을 어젯밤 당신은 제게 물으셨습니다. "
            "첫 번째는, 두 사람의 감정을 아랑곳하지 않고 제가 빙리 씨를 당신의 언니에게서 떼어 "
            "놓았다는 것이었고, 다른 하나는, 여러 권리를 짓밟고 명예와 인간됨을 짓밟으며 제가 위컴 "
            "씨의 눈앞의 번영을 무너뜨리고 그 앞날을 시들게 했다는 것이었습니다.",
    translator_id="pildam.sample", translation_status="sample_pending_human",
    mip_class="requires_prereq", prereq_spans=["pp.letter.01"],
    income_tags=["죄목","해명","공정한 판단"], viewpoint="다아시", difficulty=3,
    wildness_note="변명을 시작하면서 상대가 건 죄목을 한 자도 빼지 않고 먼저 정확히 되읊는다.")

out = {"meta": {"name": "필담 코퍼스 v2",
                "sources": {SH: sh_sha, PP: pp_sha},
                "note": "원문은 Project Gutenberg 판본에서 기계 추출(sourced). 한국어는 샘플 번역."},
       "spans": spans}
(S.parent / "x").parent  # noop
pathlib.Path("/home/user/-/project-pildam/corpus/pildam-v2.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"{len(spans)} spans")
for k, v in spans.items():
    print(f"  {k:16s} {len(v['text_ko']):4d}자ko  {len(v['text_src']):4d}ch-en  {v['locus']}")
