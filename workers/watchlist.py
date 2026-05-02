"""Watchlists used by daily_digest (P1) and mrna_lnp_watch (P2).

Single source of truth — both workers import from here so adding a
company/keyword in one place propagates everywhere.
"""
from __future__ import annotations

# mRNA / LNP / gene-editing-LNP scientific keywords.
LNP_KEYWORDS: tuple[str, ...] = (
    "lipid nanoparticle",
    "mRNA delivery",
    "ionizable lipid",
    "LNP",
    "mRNA-LNP",
    "mRNA vaccine",
    "saRNA",
    "circRNA",
    "self-amplifying RNA",
    "in vivo CAR-T",
    "base editing in vivo",
    "PEG lipid",
)

# Public companies tracked via SEC EDGAR 8-K (used in P2).
PUBLIC_TICKERS: dict[str, list[str]] = {
    # Core mRNA/LNP clinical-stage
    "core_mrna_lnp": ["MRNA", "BNTX", "ARCT", "GBIO", "RVMD", "VIR", "ALNY"],
    # Additional LNP clinical-stage (per user 2026-05-03)
    "lnp_clinical":  ["LLY", "VERV"],
    # In-vivo gene editing with LNP delivery
    "gene_editing":  ["BEAM", "NTLA", "CRSP", "EDIT", "PRME"],
}

# Acquirers — only alert if 8-K body contains the watched name.
ACQUIRERS_WITH_KEYWORD: dict[str, list[str]] = {
    "ABBV": ["Capstan"],
}

# Private companies tracked by name in news / bioRxiv author searches.
PRIVATE_COMPANIES: tuple[str, ...] = (
    "ReCode Therapeutics",
    "Capstan Therapeutics",
    "Strand Therapeutics",
    "Sail Biomedicines",
    "Orna Therapeutics",
    "Tessera Therapeutics",
    "Replicate Bioscience",
    "Ziphius Vaccines",
    "Senda Biosciences",
    "Suzhou Abogen",
    "Walvax",
    "Acuitas Therapeutics",
    "Genevant Sciences",
)


def all_public_tickers() -> list[str]:
    """Flat list of public tickers monitored via 8-K (P2)."""
    out: list[str] = []
    for tickers in PUBLIC_TICKERS.values():
        out.extend(tickers)
    out.extend(ACQUIRERS_WITH_KEYWORD.keys())
    return out
