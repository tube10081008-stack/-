# tools/build_pdf.py

국문 논문 마크다운(`paper/narrative-state-is-not-memory.ko.md`)을 조판된 PDF로 변환한다.

## 의존성

```bash
apt-get install -y fonts-nanum fonts-noto-cjk
pip install markdown weasyprint
```

## 실행

```bash
python3 tools/build_pdf.py
# → paper/서사상태는_기억이_아니다.pdf
```

표지 · 목차 · 러닝헤드 · 페이지 번호를 자동 생성하며, 표는 캡션과 함께 페이지 분할을 방지한다.
본문 서체는 Noto Serif CJK KR, 제목·표는 Noto Sans CJK KR을 사용한다.
