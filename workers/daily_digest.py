"""Daily digest worker — Phase 1 entrypoint.

Run from repo root::

    python -m workers.daily_digest

Required env vars:
    ANTHROPIC_API_KEY   — Claude API key
    GMAIL_APP_PASSWORD  — Gmail App Password (16 chars, no spaces)
    DIGEST_RECIPIENTS   — comma-separated list of recipient emails
    SMTP_USER           — sender Gmail address (default park6305@gmail.com)
    DASHBOARD_URL       — public Streamlit Cloud URL (optional)
"""
from __future__ import annotations

import json
import logging
import os
import sys
import traceback
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from shared_api.biorxiv import fetch_biorxiv
from shared_api.fda import fetch_fda_press
from shared_api.news import fetch_google_news
from workers.emailer import send_digest_email
from workers.summarizer import summarize_for_digest

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("daily_digest")

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
ARCHIVE_DIR = DATA_DIR / "archive"

CATEGORIES: dict[str, dict[str, Any]] = {
    "🏛️ FDA / 규제": {
        "fda_press": True,
        "google_queries": [
            "FDA drug approval 2025",
            "FDA NDA BLA approval",
            "EMA regulatory decision pharmaceutical",
        ],
        "biorxiv": False,
    },
    "💊 DDS / mRNA-LNP": {
        "fda_press": False,
        "google_queries": [
            "drug delivery nanoparticle 2025",
            "lipid nanoparticle mRNA delivery",
            "PLGA polymer drug delivery",
        ],
        "biorxiv": True,  # filtered to DDS-relevant categories
    },
    "🏢 Pharma Business": {
        "fda_press": False,
        "google_queries": [
            "pharma merger acquisition 2025",
            "clinical trial phase 3 results",
            "biotech licensing deal",
        ],
        "biorxiv": False,
    },
}


def _fetch_category(name: str, cfg: dict[str, Any]) -> list[dict]:
    items: list[dict] = []
    seen_titles: set[str] = set()

    if cfg.get("fda_press"):
        try:
            for it in fetch_fda_press(max_results=10):
                t = it.get("title", "")
                if t and not t.startswith("Error:") and t not in seen_titles:
                    seen_titles.add(t)
                    items.append(it)
        except Exception:
            logger.exception("FDA press fetch failed")

    for q in cfg.get("google_queries", []):
        try:
            for it in fetch_google_news(q, max_results=5):
                t = it.get("title", "")
                if t and not t.startswith("Error:") and t not in seen_titles:
                    seen_titles.add(t)
                    items.append(it)
        except Exception:
            logger.exception("Google News fetch failed for %r", q)

    if cfg.get("biorxiv"):
        try:
            for it in fetch_biorxiv(days_back=2, max_results=15):
                t = it.get("title", "")
                if t and not t.startswith("Error:") and t not in seen_titles:
                    seen_titles.add(t)
                    items.append(it)
        except Exception:
            logger.exception("bioRxiv fetch failed")

    logger.info("[%s] collected %d items", name, len(items))
    return items


def _build_digest(api_key: str) -> dict[str, Any]:
    raw_by_cat: dict[str, list[dict]] = {
        name: _fetch_category(name, cfg) for name, cfg in CATEGORIES.items()
    }
    total = sum(len(v) for v in raw_by_cat.values())
    by_source = Counter(it.get("source", "?") for items in raw_by_cat.values() for it in items)

    if total == 0:
        raise RuntimeError("All sources returned 0 items — aborting digest.")

    logger.info("calling Claude summarizer (total=%d items)", total)
    summary = summarize_for_digest(raw_by_cat, api_key=api_key)

    digest = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "trend_summary_ko": summary.get("trend_summary_ko", ""),
        "highlights": summary.get("highlights", []),
        "categories": raw_by_cat,
        "stats": {"total": total, "by_source": dict(by_source)},
        "dashboard_url": os.getenv("DASHBOARD_URL", ""),
    }
    return digest


def _write_outputs(digest: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    latest = DATA_DIR / "digest_latest.json"
    archive = ARCHIVE_DIR / f"{digest['generated_at'][:10]}.json"
    payload = json.dumps(digest, ensure_ascii=False, indent=2)
    latest.write_text(payload, encoding="utf-8")
    archive.write_text(payload, encoding="utf-8")
    logger.info("wrote %s and %s", latest, archive)


def main() -> int:
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    smtp_password = os.getenv("GMAIL_APP_PASSWORD", "").strip()
    smtp_user = os.getenv("SMTP_USER", "park6305@gmail.com").strip()
    recipients_raw = os.getenv("DIGEST_RECIPIENTS", smtp_user).strip()

    if not api_key:
        logger.error("ANTHROPIC_API_KEY is missing")
        return 2
    if not smtp_password:
        logger.error("GMAIL_APP_PASSWORD is missing")
        return 2

    try:
        digest = _build_digest(api_key)
    except Exception:
        traceback.print_exc()
        return 3

    try:
        _write_outputs(digest)
    except Exception:
        logger.exception("failed to write outputs")
        return 4

    recipients = [r.strip() for r in recipients_raw.split(",") if r.strip()]
    try:
        send_digest_email(digest, recipients, smtp_user=smtp_user, smtp_password=smtp_password)
    except Exception:
        logger.exception("failed to send email (digest JSON was written)")
        return 5

    logger.info("done — total=%d highlights=%d", digest["stats"]["total"], len(digest["highlights"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
