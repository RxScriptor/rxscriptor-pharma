"""FDA Press Announcements RSS fetcher.

Returns items in the same dict shape as ``shared_api.news.fetch_google_news``:
``{title, link, date (YYYY.MM.DD), source, desc}``.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Dict, List

import feedparser

FDA_PRESS_RSS = (
    "https://www.fda.gov/AboutFDA/ContactFDA/StayInformed/RSSFeeds/"
    "PressReleases/rss.xml"
)
USER_AGENT = "Mozilla/5.0 (rxscriptor-dashboard)"
_TAG_RE = re.compile(r"<[^>]+>")


def fetch_fda_press(max_results: int = 10) -> List[Dict]:
    """Return up to ``max_results`` FDA press announcements.

    On network/parse error returns a single sentinel item with
    ``title`` prefixed ``Error:``.
    """
    feed = feedparser.parse(FDA_PRESS_RSS, agent=USER_AGENT)
    if feed.bozo and not feed.entries:
        return [
            {
                "title": f"Error: {feed.bozo_exception}",
                "link": "#",
                "date": "",
                "source": "FDA Press",
                "desc": "",
            }
        ]

    items: List[Dict] = []
    seen: set[str] = set()
    for entry in feed.entries[:max_results]:
        title = (entry.get("title") or "").strip()
        if not title or title in seen:
            continue
        seen.add(title)

        desc = _TAG_RE.sub("", entry.get("summary", ""))[:250].strip()

        date_str = ""
        published = entry.get("published_parsed")
        if published:
            try:
                date_str = datetime(*published[:6]).strftime("%Y.%m.%d")
            except (ValueError, TypeError):
                pass
        if not date_str:
            date_str = (entry.get("published") or "")[:10]

        items.append(
            {
                "title": title,
                "link": entry.get("link", "#"),
                "date": date_str,
                "source": "FDA Press",
                "desc": desc,
            }
        )
    return items


if __name__ == "__main__":
    for it in fetch_fda_press(5):
        print(f"[{it['date']}] {it['title']}")
        print(f"  {it['link']}")
