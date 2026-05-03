"""P3 daily DART disclosure watcher.

For each ticker in `companies/_index.json`, fetches new DART filings since
the last seen rcept_no, classifies them with a Haiku call, appends to
`data/company_events/<ticker>.jsonl` (append-only event log), and writes
inbox drafts to `data/company_inbox/` for human review.

The worker NEVER edits `companies/<ticker>.md` — those are curator territory.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from anthropic import Anthropic

from .dart_client import DartClient, Filing


REPO_ROOT = Path(__file__).resolve().parent.parent
COMPANIES_DIR = REPO_ROOT / "companies"
INDEX_PATH = COMPANIES_DIR / "_index.json"
EVENTS_DIR = REPO_ROOT / "data" / "company_events"
INBOX_DIR = REPO_ROOT / "data" / "company_inbox"

DEFAULT_BACKFILL_DAYS = 90
DEFAULT_IMPORTANCE_THRESHOLD = 3
CLASSIFIER_MODEL = "claude-haiku-4-5-20251001"

CATEGORIES = [
    "임상시험", "라이선스/M&A", "자본·증자", "실적",
    "신약승인", "인사·지배구조", "기타",
]


def load_index() -> dict:
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


def save_index(idx: dict) -> None:
    idx["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    INDEX_PATH.write_text(
        json.dumps(idx, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def classify(client: Anthropic, filing: Filing, body: str, name_ko: str) -> dict:
    prompt = f"""다음은 한국 상장사 DART 공시입니다. 분류해주세요.

회사: {name_ko}
공시 제목: {filing.report_nm}
공시일: {filing.rcept_dt}
신고인: {filing.flr_nm}
비고: {filing.rm}
본문 일부:
{body[:5000]}

다음 JSON 형식으로만 응답 (다른 텍스트 금지):
{{
  "category": "<{', '.join(CATEGORIES)} 중 1>",
  "ko_summary_2line": "<2줄 한국어, 파이프라인/임상/라이선스 구체값 우선>",
  "importance": <0-10 정수, 파이프라인·주가 영향>,
  "tags": ["<modality나 핵심 키워드 1-3개>"]
}}"""
    resp = client.messages.create(
        model=CLASSIFIER_MODEL,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    text = resp.content[0].text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 2:
            text = parts[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        out = json.loads(text)
    except json.JSONDecodeError:
        return {
            "category": "기타",
            "ko_summary_2line": filing.report_nm,
            "importance": 0,
            "tags": [],
        }
    out.setdefault("category", "기타")
    out.setdefault("ko_summary_2line", filing.report_nm)
    out.setdefault("importance", 0)
    out.setdefault("tags", [])
    return out


def append_event(ticker: str, filing: Filing, classified: dict) -> None:
    EVENTS_DIR.mkdir(parents=True, exist_ok=True)
    line = json.dumps(
        {
            "rcept_no": filing.rcept_no,
            "rcept_dt": filing.rcept_dt,
            "report_nm": filing.report_nm,
            "category": classified["category"],
            "importance": classified["importance"],
            "ko_summary_2line": classified["ko_summary_2line"],
            "tags": classified["tags"],
            "url": filing.url,
        },
        ensure_ascii=False,
    )
    with (EVENTS_DIR / f"{ticker}.jsonl").open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def write_inbox(
    ticker: str, name_ko: str, filing: Filing, classified: dict
) -> Path:
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    iso_date = f"{filing.rcept_dt[:4]}-{filing.rcept_dt[4:6]}-{filing.rcept_dt[6:8]}"
    fname = f"{iso_date}_{ticker}_{filing.rcept_no}.md"
    path = INBOX_DIR / fname
    timeline_line = (
        f"- **{iso_date}** — {classified['category']}: "
        f"{classified['ko_summary_2line']} ([원문]({filing.url}))"
    )
    body = f"""**Ticker**: {ticker} {name_ko}
**공시일**: {iso_date} (rcept_no: {filing.rcept_no})
**유형**: {filing.report_nm}
**카테고리**: {classified['category']}
**중요도**: {classified['importance']}/10
**태그**: {', '.join(classified['tags']) or '-'}

**요약**:
{classified['ko_summary_2line']}

**원문**: {filing.url}

---

**Append to** `companies/{ticker}_*.md` §2 timeline (맨 위):

```
{timeline_line}
```
"""
    path.write_text(body, encoding="utf-8")
    return path


def yyyymmdd(d) -> str:
    return d.strftime("%Y%m%d")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="DART daily watcher (P3 companies portfolio)"
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="fetch + classify but do not write files or update index",
    )
    p.add_argument(
        "--backfill-days",
        type=int,
        default=DEFAULT_BACKFILL_DAYS,
        help="how far back to look on first run (no last_seen_rcept_no)",
    )
    p.add_argument(
        "--importance-threshold",
        type=int,
        default=DEFAULT_IMPORTANCE_THRESHOLD,
        help="minimum importance to write inbox draft (events log gets all)",
    )
    p.add_argument(
        "--ticker",
        action="append",
        help="only process specified ticker(s); default: all in _index.json",
    )
    args = p.parse_args(argv)

    api_key = os.environ.get("DART_API_KEY")
    if not api_key:
        print("ERROR: DART_API_KEY not set", file=sys.stderr)
        return 2
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if not anthropic_key:
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        return 2

    dart = DartClient(api_key)
    llm = Anthropic(api_key=anthropic_key)

    idx = load_index()
    companies = idx["companies"]

    need_resolution = [
        t for t, info in companies.items()
        if not info.get("corp_code")
        and (not args.ticker or t in args.ticker)
    ]
    if need_resolution:
        print(f"Resolving corp_codes for {len(need_resolution)} ticker(s)...")
        stock_to_corp = dart.fetch_corp_codes()
        for ticker in need_resolution:
            corp = stock_to_corp.get(ticker)
            if not corp:
                print(f"  WARN: no corp_code for {ticker}", file=sys.stderr)
                continue
            companies[ticker]["corp_code"] = corp
            print(f"  {ticker} -> corp_code {corp}")

    today = datetime.now(timezone.utc).date()
    end_de = yyyymmdd(today)
    new_filings_total = 0
    drafts_written = 0

    for ticker, info in companies.items():
        if args.ticker and ticker not in args.ticker:
            continue
        corp = info.get("corp_code")
        if not corp:
            print(f"[{ticker}] skip (no corp_code)")
            continue
        last_seen = info.get("last_seen_rcept_no")
        bgn_de = (
            last_seen[:8]
            if last_seen
            else yyyymmdd(today - timedelta(days=args.backfill_days))
        )

        print(f"[{ticker}] {info['name_ko']}: list {bgn_de}..{end_de}")

        new_filings: list[Filing] = []
        for filing in dart.list_filings(corp, bgn_de, end_de):
            if last_seen and filing.rcept_no <= last_seen:
                continue
            new_filings.append(filing)

        if not new_filings:
            print("  no new filings")
            continue
        print(f"  {len(new_filings)} new filing(s)")
        new_filings_total += len(new_filings)

        new_filings.sort(key=lambda f: f.rcept_no)

        for filing in new_filings:
            body = dart.fetch_document_text(filing.rcept_no)
            classified = classify(llm, filing, body, info["name_ko"])
            print(
                f"  {filing.rcept_no} | {classified['category']} | "
                f"imp={classified['importance']} | {filing.report_nm[:40]}"
            )
            if args.dry_run:
                continue
            append_event(ticker, filing, classified)
            if classified["importance"] >= args.importance_threshold:
                write_inbox(ticker, info["name_ko"], filing, classified)
                drafts_written += 1

        if not args.dry_run:
            info["last_seen_rcept_no"] = new_filings[-1].rcept_no
            info["last_polled_at"] = datetime.now(timezone.utc).isoformat(
                timespec="seconds"
            )

    if not args.dry_run:
        save_index(idx)

    print(
        f"\nDone: {new_filings_total} new filings across portfolio, "
        f"{drafts_written} inbox draft(s) written"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
