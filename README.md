# rxscriptor-pharma

**Layer 2A Brand · Public**
Streamlit 앱 — Pharma News & AI Trend Dashboard

Google News RSS → 트렌드 분석 → Claude API 요약. FDA/EMA · DDS · Pharma Business 카테고리.

## 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 배포 (Streamlit Cloud)

1. Public repo 연결
2. Secrets에 `ANTHROPIC_API_KEY` 등록
3. Deploy

## P3 트랙 — 회사 포트폴리오 + DART 공시 워커

회사 단위 산업동향 추적. 한국 6개사 (`companies/`)부터 시작:
**006280** 녹십자, **128940** 한미약품, **000100** 유한양행, **326030** SK바이오팜, **068270** 셀트리온, **185750** 종근당.

### 작동 방식

매일 09:00 KST에 `.github/workflows/dart_watch.yml`이 실행 →
`workers/dart_watch.py`가 각 회사의 신규 DART 공시를 조회 →
Gemini 2.5 Flash로 카테고리/중요도/2줄 요약 생성 →
- **모든 공시** → `data/company_events/<ticker>.jsonl` (append-only, 분석용)
- **importance ≥ 3** → `data/company_inbox/<date>_<ticker>_<rcept>.md` (큐레이션 큐)

`companies/<ticker>.md`은 워커가 **절대** 건드리지 않음 — 큐레이터 영역.

### 큐레이션 워크플로

매일 (또는 주 1회):
1. `git pull`
2. `data/company_inbox/` 신규 draft 확인
3. 각 draft의 "Append to" 블록을 해당 `companies/<ticker>.md` §2 timeline 맨 위에 복붙
4. 필요시 §1 pipeline / §4 financial signal 갱신
5. inbox draft 삭제 (또는 후속 prune workflow가 처리)
6. `git commit -m "docs(companies): ..."` → `git push`

### Secret 등록 (Repo Settings → Secrets and variables → Actions)

- `DART_API_KEY` — [opendart.fss.or.kr](https://opendart.fss.or.kr) 가입 후 발급 (무료)
- `GEMINI_API_KEY` — [aistudio.google.com](https://aistudio.google.com/apikey) 발급. 워커는 `gemini-2.5-flash` 사용 (free tier 5 RPM, project-default RPD 안에서 동작; PerDay 소진 시 graceful exit)

### 로컬 테스트

```bash
export DART_API_KEY=...
export GEMINI_API_KEY=...
python -m workers.dart_watch --dry-run --ticker 128940 --backfill-days 30
```

`--dry-run`은 fetch + classify만 하고 파일 쓰기/index 갱신 안 함 — 첫 실행 비용 가늠용.

### 첫 운영 (수동 트리거)

PR merge → Secret 등록 → GitHub Actions 탭 → "dart-watch" → "Run workflow" →
첫 90일 backfill 1회 실행 (6 ticker × 평균 30 공시 = 약 180 LLM call, free tier 한도 내).

## 관련 repo

- [RxScriptor](https://github.com/RxScriptor/RxScriptor) — Brand Root (디자인 토큰 SSOT)
- [rxscriptor-literature](https://github.com/RxScriptor/rxscriptor-literature) — 자매 Streamlit 앱 (논문 요약)

From Bench. Written in Code.
