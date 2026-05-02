"""Shared runtime fetchers for pharma news."""
from .biorxiv import fetch_biorxiv
from .fda import fetch_fda_press
from .news import fetch_google_news

__all__ = [
    "fetch_biorxiv",
    "fetch_fda_press",
    "fetch_google_news",
]
