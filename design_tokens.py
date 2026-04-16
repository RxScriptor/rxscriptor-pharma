"""Load RxScript design tokens from the JSON single-source-of-truth.

The JSON lives alongside this module in the deployed Streamlit app repo.
Keep in sync with `RxScriptor` Brand Root repo when design tokens change.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent
_TOKENS_PATH = _REPO_ROOT / "rxscript-tokens.json"


def load_tokens() -> dict[str, Any]:
    with _TOKENS_PATH.open(encoding="utf-8") as f:
        return json.load(f)


_TOKENS = load_tokens()

COLOR: dict[str, str] = _TOKENS["color"]
FONT: dict[str, str] = _TOKENS["font"]
WEIGHT: dict[str, int] = _TOKENS["weight"]
SPACE: dict[str, str] = _TOKENS["space"]
RADIUS: dict[str, str] = _TOKENS["radius"]
