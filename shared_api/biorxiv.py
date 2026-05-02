"""bioRxiv API fetcher for daily preprints in selected categories.

Uses the public details API at
``https://api.biorxiv.org/details/{server}/{from_date}/{to_date}/{cursor}``.

Returns items in the same dict shape as ``shared_api.news.fetch_google_news``.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional

import requests

BIORXIV_API = "https://api.biorxiv.org/details/{server}/{from_date}/{to_date}/{cursor}"

# Categories most relevant to DDS / mRNA-LNP / pharma R&D.
# bioRxiv category strings are lowercase per the API.
DEFAULT_CATEGORIES = frozenset(
    {
        "pharmacology and toxicology",
        "bioinformatics",
        "systems biology",
        "biophysics",
        "biochemistry",
        "molecular biology",
        "genetics",
        "cell biology",
        "immunology",
        "synthetic biology",
        "bioengineering",
    }
)
USER_AGENT = "rxscriptor-dashboard"


def fetch_biorxiv(
    server: str = "biorxiv",
    days_back: int = 1,
    categories: Optional[Iterable[str]] = None,
    max_results: int = 30,
    timeout: int = 15,
) -> List[Dict]:
    """Fetch bioRxiv preprints posted within the last ``days_back`` days.

    Filters by ``categories`` (case-insensitive). bioRxiv's API paginates
    by 100; we walk pages until ``max_results`` items match or we have
    scanned 5 pages (500 candidates).
    """
    today = datetime.now(timezone.utc).date()
    from_date = (today - timedelta(days=days_back)).isoformat()
    to_date = today.isoformat()
    cats = {c.lower() for c in (categories or DEFAULT_CATEGORIES)}

    items: List[Dict] = []
    seen: set[str] = set()
    cursor = 0

    try:
        while len(items) < max_results and cursor < 500:
            url = BIORXIV_API.format(
                server=server, from_date=from_date, to_date=to_date, cursor=cursor
            )
            r = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
            r.raise_for_status()
            payload = r.json()
            collection = payload.get("collection") or []
            if not collection:
                break

            for paper in collection:
                category = (paper.get("category") or "").lower()
                if category not in cats:
                    continue
                doi = (paper.get("doi") or "").strip()
                if not doi or doi in seen:
                    continue
                seen.add(doi)

                title = (paper.get("title") or "").strip()
                desc = (paper.get("abstract") or "")[:250].strip()
                date_str = (paper.get("date") or "").replace("-", ".")
                items.append(
                    {
                        "title": title,
                        "link": f"https://www.biorxiv.org/content/{doi}v1",
                        "date": date_str,
                        "source": f"bioRxiv {paper.get('category', '')}".strip(),
                        "desc": desc,
                    }
                )
                if len(items) >= max_results:
                    break

            cursor += 100
        return items
    except requests.RequestException as e:
        return [
            {
                "title": f"Error: {e}",
                "link": "#",
                "date": "",
                "source": "bioRxiv",
                "desc": "",
            }
        ]


if __name__ == "__main__":
    for it in fetch_biorxiv(days_back=2, max_results=5):
        print(f"[{it['date']}] {it['source']}")
        print(f"  {it['title']}")
        print(f"  {it['link']}")
