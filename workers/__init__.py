"""Background workers for scheduled news collection and notification.

Tier 2: daily_digest — runs once per day, fetches multi-source pharma news,
summarizes via Claude, and emails a Korean digest.
Tier 1 (Phase 2): mrna_lnp_watch — polls every 15 min for new mRNA/LNP signals,
sends Telegram alerts.
"""
