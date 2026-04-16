"""Google News RSS fetcher."""
from __future__ import annotations

import re
import urllib.parse
from datetime import datetime

import requests

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
USER_AGENT = "Mozilla/5.0 (rxscriptor-dashboard)"


def fetch_google_news(query: str, max_results: int = 8) -> list[dict]:
    """Return up to `max_results` de-duplicated news items for `query`.

    Each item: {title, link, date (YYYY.MM.DD), source, desc}.
    On network error returns a single item with title="Error: ...".
    """
    url = GOOGLE_NEWS_RSS.format(q=urllib.parse.quote(query))
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": USER_AGENT})
        r.raise_for_status()
        items: list[dict] = []
        seen: set[str] = set()
        for entry in re.findall(r"<item>(.*?)</item>", r.text, re.DOTALL)[:max_results]:
            title_m   = re.search(r"<title>(.*?)</title>", entry)
            link_m    = re.search(r"<link>(.*?)</link>", entry)
            pubdate_m = re.search(r"<pubDate>(.*?)</pubDate>", entry)
            source_m  = re.search(r"<source[^>]*>(.*?)</source>", entry)
            desc_m    = re.search(r"<description>(.*?)</description>", entry, re.DOTALL)

            title   = re.sub(r"<[^>]+>", "", title_m.group(1))   if title_m   else ""
            link    = link_m.group(1).strip()                    if link_m    else "#"
            pubdate = pubdate_m.group(1).strip()                 if pubdate_m else ""
            source  = source_m.group(1).strip()                  if source_m  else ""
            desc    = re.sub(r"<[^>]+>", "", desc_m.group(1))[:200] if desc_m else ""

            try:
                dt = datetime.strptime(pubdate[:25], "%a, %d %b %Y %H:%M:%S")
                date_str = dt.strftime("%Y.%m.%d")
            except ValueError:
                date_str = pubdate[:10]

            if title and title not in seen:
                seen.add(title)
                items.append({
                    "title": title, "link": link, "date": date_str,
                    "source": source, "desc": desc,
                })
        return items
    except requests.RequestException as e:
        return [{"title": f"Error: {e}", "link": "#", "date": "", "source": "", "desc": ""}]
