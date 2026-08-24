# rxscriptor-pharma — Brand App Context

> 위치: `rxscriptor-pharma/CLAUDE.md`
> Layer: 2A (Brand, Public)

---

## 0. This App

**앱**: Pharma News & AI Trend Dashboard + 일일 자동 다이제스트
**용도**:
1. **대시보드** (on-demand): Google News RSS → 사용자 클릭 시 Claude 요약
2. **T2 일일 다이제스트** (자동): 매일 08:00 KST GitHub Actions로 Google News + FDA Press + bioRxiv → Sonnet 4.6 한국어 요약 → 이메일 + JSON 영속화 → 대시보드 노출
3. **T1 mRNA/LNP 실시간** (Phase 2): 15분 polling, Telegram 알림 (예정)

**카테고리**: FDA/규제 · DDS/mRNA-LNP · Pharma Business
**메인 파일**: `app.py` (대시보드), `workers/daily_digest.py` (워커)
**배포**: Streamlit Cloud (대시보드) + GitHub Actions (워커)

### 파일 구조 메모 (ls로 안 보이는 것만)

- `workers/watchlist.py` = SSOT — ticker / 키워드 / 회사명.
- `data/` 는 워커가 commit하는 영속 데이터 — 첫 실행 전엔 `archive/.gitkeep`만 존재하므로 `digest_latest.json` 부재는 정상.

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

HEX 값은 `rxscript-tokens.json` (Brand Root SSOT 복사본) 참조.

### 색상 규칙
- **Rx** → 항상 Navy `#1A2E5A`
- **Scriptor** → 항상 Red `#E8365D`
- 슬로건 → Navy, uppercase
- 서브라인 → Muted

---

## 3. 타이포그래피

폰트 배정은 `rxscript-tokens.json` 참조 (wordmark 2종 + 본문 + 한국어).

---

## 4. 필수 모듈: rxscriptor_header.py

모든 Streamlit 앱은 이 모듈 사용. 직접 CSS·HTML 작성 금지. 제공 함수 목록은 `rxscriptor_header.py` 참조.

호출 순서 규칙: `apply_theme(mode="light")`는 **반드시 `st.set_page_config()` 직후** — 순서가 어긋나면 테마가 조용히 미적용.

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

### 모델 (사용처별 분리)

| 사용처 | 모델 | 이유 |
|--------|------|------|
| 대시보드 on-demand 요약 (`app.py`) | `claude-opus-4-6` | 기존 유지 |
| T2 일일 다이제스트 (`workers/summarizer.py`) | `claude-sonnet-4-6` | 비용/속도 균형, prompt caching 적용 |
| T1 mRNA/LNP 필터 (P2 예정) | `claude-haiku-4-5-20251001` | 고빈도 폴링, 신규건만 통과 |

워커 모델은 env var `DIGEST_MODEL`로 오버라이드 가능.

### API Key
우선순위: Streamlit Cloud Secrets → 사용자 입력 fallback (구현은 `app.py`).
워커는 `os.getenv("ANTHROPIC_API_KEY")` (GitHub Actions Secret).

### 프롬프트
- 한국어 응답 명시
- "Pharmaceutical Researcher" 역할
- DDS, CMC, PK/PD 도메인 컨텍스트
- JSON 출력 시 형식 명확
- 시스템 프롬프트는 `cache_control: ephemeral`로 프롬프트 캐싱 활용 (워커)

---

## 7. 배포 — Streamlit Cloud 표준 절차 (share.streamlit.io, Secrets에 `ANTHROPIC_API_KEY`). `.streamlit/secrets.toml` 커밋 금지는 §9 보안 참조.

---

## 8. (참고·별도 repo) rxscriptor-literature 전용 — Zotero 연동 (예정)

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
