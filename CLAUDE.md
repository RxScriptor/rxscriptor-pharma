# rxscriptor-pharma — Brand App Context

> 위치: `rxscriptor-pharma/CLAUDE.md`
> Layer: 2A (Brand, Public)

---

## 0. This App

**앱**: Pharma News & AI Trend Dashboard + 회사 포트폴리오 (P3 트랙)
**용도**:
- Streamlit on-demand: Google News RSS → 트렌드 분석 → Claude AI 요약 (FDA/EMA · DDS · Pharma Business)
- **P3 트랙 (백그라운드 워커)**: 매일 09:00 KST DART 공시 크롤링 → 회사별 event jsonl + 큐레이션 inbox draft
**메인 파일**: `app.py` (Streamlit), `workers/dart_watch.py` (P3)
**배포**: Streamlit Cloud (앱), GitHub Actions (P3 워커)

### 트랙 구조

| 트랙 | 출처 | 산출물 | 주기 | 상태 |
|------|------|--------|------|------|
| **P3 (회사 포트폴리오)** | DART OpenAPI | `data/company_events/`, `data/company_inbox/`, `companies/` | 일 1회 09:00 KST | 활성 |
| P1 (산업 다이제스트) | FDA/Google News/bioRxiv | 매일 이메일 + dashboard 섹션 | 일 1회 | spec only |
| P2 (mRNA/LNP 실시간) | bioRxiv/SEC/PubMed | Telegram push | 15분 | spec only |

### 파일 구조

```
rxscriptor-pharma/
├── app.py                      메인 Streamlit 앱 (on-demand)
├── rxscriptor_header.py        Clinical White 테마 헤더/footer
├── design_tokens.py            rxscript-tokens.json 로더
├── rxscript-tokens.json        디자인 토큰 (Brand Root SSOT 복사본)
├── shared_api/
│   ├── __init__.py
│   └── news.py                 Google News RSS
├── workers/                    [P3] 백그라운드 워커
│   ├── __init__.py
│   ├── dart_client.py          DART OpenAPI 클라이언트
│   └── dart_watch.py           일일 공시 워처 + Haiku 분류기
├── companies/                  [P3] 회사 포트폴리오
│   ├── _template.md
│   ├── _index.json             ticker→corp_code, last_seen_rcept_no SSOT
│   └── <ticker>_<name>.md      6 KR 회사 stub (큐레이터 영역, 워커 read-only)
├── data/                       [P3] 워커 산출물 (git-tracked)
│   ├── company_events/         <ticker>.jsonl append-only
│   └── company_inbox/          <date>_<ticker>_<rcept>.md draft 큐
├── .github/workflows/
│   └── dart_watch.yml          [P3] cron 09:00 KST + workflow_dispatch
├── .streamlit/config.toml
├── requirements.txt
└── README.md
```

### 디자인 토큰 동기화 규칙

`rxscript-tokens.json`은 `RxScriptor` Brand Root의
`design-systems/rxscript/tokens/rxscript-tokens.json` 복사본.
**Brand Root에서 토큰이 변경되면 여기도 수동 복사**. 반대 방향 금지.

---

## 1. 브랜드 정보 (고정)

- **브랜드**: RxScriptor
- **슬로건**: From Bench. Written in Code.
- **서브라인**: Pharmaceutical Researcher × AI Developer
- **GitHub**: github.com/rxscriptor

---

## 2. Clinical White 테마 (필수)

| 역할 | HEX |
|------|-----|
| Background | `#F8F9FC` |
| Primary (Navy) | `#1A2E5A` |
| Accent (Red) | `#E8365D` |
| Secondary (Steel) | `#5B8DB8` |
| Muted | `#828C9B` |
| Border | `#DDE0ED` |

### 색상 규칙
- **Rx** → 항상 Navy `#1A2E5A`
- **Scriptor** → 항상 Red `#E8365D`
- 슬로건 → Navy, uppercase
- 서브라인 → Muted

---

## 3. 타이포그래피

| 역할 | 폰트 |
|------|------|
| Rx wordmark | Syne 800 |
| Scriptor wordmark | Crimson Pro 600 Italic |
| 본문 | DM Mono |
| 한국어 | Noto Sans KR |

---

## 4. 필수 모듈: rxscriptor_header.py

모든 Streamlit 앱은 이 모듈 사용. 직접 CSS·HTML 작성 금지.

```python
from rxscriptor_header import (
    apply_theme, show_header, show_mini_header,
    section_title, info_card, tag_badges, show_footer,
)
```

### 표준 앱 구조

```python
import streamlit as st
from rxscriptor_header import (...)

st.set_page_config(
    page_title="RxScriptor · <앱명>",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme(mode="light")   # 반드시 set_page_config 직후

with st.sidebar:
    show_mini_header()
    # ...

show_header(subtitle="<앱 부제목>")
# ...
show_footer()
```

---

## 5. UI 컴포넌트 규칙

### 카드
- 배경: White 또는 `#F8F9FC`
- 테두리: `#DDE0ED` 1px
- 강조선: left 3px 또는 top 3px
- 그림자: 은은한 rgba(26,46,90,.04~.08)

### 버튼
- 기본: Navy border, transparent 배경
- Primary: Navy 배경, 흰 텍스트, hover → Red

### 섹션
`section_title(label, title)` 사용 — label 소문자 영문, title 한국어/영문

---

## 6. Claude API

### 모델
| 사용처 | 모델 |
|--------|------|
| 앱 on-demand 개별 요약 | `claude-opus-4-6` |
| P3 DART 공시 분류 (`workers/dart_watch.py`) | `claude-haiku-4-5-20251001` |

### API Key
```python
api_key = st.secrets.get("ANTHROPIC_API_KEY", "") or st.text_input(
    "API Key", type="password", label_visibility="collapsed"
)
```

우선순위: Streamlit Cloud Secrets → 사용자 입력 fallback

### 프롬프트
- 한국어 응답 명시
- "Pharmaceutical Researcher" 역할
- DDS, CMC, PK/PD 도메인 컨텍스트
- JSON 출력 시 형식 명확

---

## 7. 배포 (Streamlit Cloud)

1. GitHub Public repo에 push
2. `requirements.txt`, `.streamlit/config.toml` 포함
3. `.streamlit/secrets.toml` **절대 커밋 금지**
4. share.streamlit.io 접속
5. Secrets에 `ANTHROPIC_API_KEY` 등록
6. Deploy

---

## 8. rxscriptor-literature 전용 — Zotero 연동 (예정)

Tier 1 수집 도구 역할 강화:
- Zotero Web API 연결
- 논문 메타데이터 crawling
- 로컬 DB 또는 Streamlit session으로 관리
- 선별된 항목 → literature-archive 이관 가이드 제공

---

## 9. 보안

- `secrets.toml` → `.gitignore`
- API key 하드코딩 금지
- 사용자 입력 API key → session state만, 로그 금지
- 회사명·내부 프로젝트명 노출 금지 (Public repo)

---

## 10. 개발 금지사항

| 금지 | 이유 |
|------|------|
| Clinical White 외 색상 | 브랜드 일관성 |
| rxscriptor_header 미사용 | 유지보수 |
| 회사 데이터 포함 | Public repo |
| API key 하드코딩 | 보안 |
| Rx를 Red로, Scriptor를 비이탤릭으로 | 절대 금지 |

---

## 11. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-04-16 | v2 — rxscriptor-literature에 Zotero 연동 역할 추가 |
| 2026-05-03 | v3 — P3 트랙 (회사 포트폴리오 + DART 공시 워커) 추가 |
