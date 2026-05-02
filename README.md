# rxscriptor-pharma

**Layer 2A Brand · Public**
Streamlit 앱 — Pharma News & AI Trend Dashboard
+ 일일 자동 다이제스트 (이메일).

다중 소스 (Google News · FDA Press · bioRxiv) → Claude AI 한국어 요약 → 매일 08:00 KST 메일 + 대시보드 업데이트.
카테고리: FDA/규제 · DDS/mRNA-LNP · Pharma Business.

---

## 1. 대시보드 실행 (로컬)

```bash
pip install -r requirements.txt
streamlit run app.py
```

`data/digest_latest.json`이 있으면 헤더 아래 "오늘의 다이제스트" 섹션이 자동 노출.

---

## 2. 배포 (Streamlit Cloud)

1. Public repo 연결
2. Secrets에 `ANTHROPIC_API_KEY` 등록 (앱 on-demand 요약용)
3. Deploy

대시보드는 워커가 commit한 `data/digest_latest.json`을 read-only로 표시. 워커가 push하면 Streamlit Cloud가 자동 재배포 (수동 reboot 필요 시 `share.streamlit.io` → 앱 메뉴 → Reboot).

---

## 3. 일일 다이제스트 워커 (T2)

### 3.1 동작

`workers/daily_digest.py`가 GitHub Actions에서 매일 23:00 UTC (08:00 KST)에 실행.

1. Google News RSS · FDA Press RSS · bioRxiv API에서 카테고리별 fetch
2. Claude Sonnet 4.6에 한 번 호출 → 한국어 트렌드 요약 + 5–10건 하이라이트
3. `data/digest_latest.json` + `data/archive/{YYYY-MM-DD}.json` 작성 후 commit & push
4. Gmail SMTP로 HTML 이메일 발송 (Clinical White 인라인 CSS)

### 3.2 사전 준비 (1회)

| Secret / Variable | 값 | 등록 위치 |
|-------------------|----|-----------|
| `ANTHROPIC_API_KEY` | Claude API key (`sk-ant-...`) | Settings → Secrets and variables → Actions → New repository secret |
| `GMAIL_APP_PASSWORD` | 16자 App Password | (위와 동일) |
| `DIGEST_RECIPIENTS` | 콤마 구분 수신자 (`a@x.com,b@y.com`) | (위와 동일) |
| `SMTP_USER` | 발신 Gmail (예: `park6305@gmail.com`) | (위와 동일) |
| `DASHBOARD_URL` | Streamlit Cloud 공개 URL | Settings → Secrets and variables → Actions → Variables 탭 |

**Gmail App Password 발급**: myaccount.google.com → Security → 2-Step Verification → App passwords → "Mail"용 16자 비밀번호 생성. 일반 계정 비밀번호 절대 사용 금지.

### 3.3 첫 실행 (수동 트리거)

위 Secrets 등록 후:

```bash
gh workflow run daily-digest.yml -R RxScriptor/rxscriptor-pharma
```

또는 GitHub UI → Actions → daily-digest → "Run workflow".

성공 시:
- 받은편지함에 한국어 다이제스트 메일
- repo에 `data/digest_latest.json` + `data/archive/{date}.json` 커밋
- Streamlit Cloud 대시보드에 다이제스트 섹션 노출

---

## 4. 보안

- Secrets는 Streamlit Cloud + GitHub Actions 양쪽에 분리 등록 (`ANTHROPIC_API_KEY` 양쪽 모두 필요)
- App Password는 절대 평문으로 저장/공유 금지
- Public repo이므로 회사명·내부 코드명 포함 금지 (워치리스트는 학술/공개사 한정)

---

## 5. 관련 repo

- [RxScriptor](https://github.com/RxScriptor/RxScriptor) — Brand Root (디자인 토큰 SSOT)
- [rxscriptor-literature](https://github.com/RxScriptor/rxscriptor-literature) — 자매 Streamlit 앱 (논문 요약)

From Bench. Written in Code.
