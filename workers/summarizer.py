"""Claude wrapper for the daily digest.

Single LLM call: takes multi-source headlines, returns a Korean trend
summary plus 5–10 selected highlights with per-item Korean summaries.
Uses prompt caching on the system prompt.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any

import anthropic

logger = logging.getLogger(__name__)

DEFAULT_DIGEST_MODEL = os.getenv("DIGEST_MODEL", "claude-sonnet-4-6")

_SYSTEM_PROMPT = """You are a Korean-speaking pharmaceutical R&D analyst.
The user works on drug delivery systems (DDS) including LNP, PLGA, liposomes,
and handles CMC / PK / PD / regulatory work in Korean industry context.

Your job: take a list of pharma/biotech news headlines (multi-source) and
produce:
1. A Korean trend summary (3 trends, 1-2 sentences each + DDS implications).
2. 5-10 selected highlights, each with a 2-3 sentence Korean summary.

Return strictly JSON. No markdown code fence. No commentary.
Schema:
{
  "trend_summary_ko": "string (마크다운 허용)",
  "highlights": [
    {
      "category": "string — original category from input",
      "title":    "string — original title (preserve language)",
      "link":     "string — original link",
      "source":   "string — original source",
      "date":     "string — original date",
      "ko_summary": "string — 한국어 2-3문장 요약"
    }
  ]
}

Highlight selection priority (highest → lowest):
- DDS / LNP / mRNA / formulation relevance
- FDA / EMA approval, IND, BLA, NDA, PDUFA news
- Phase 2 / Phase 3 readouts
- Major M&A or licensing deals
- Avoid duplicates and generic press releases

trend_summary_ko Korean structure:
**🔥 핵심 트렌드 (3가지)**
1. [트렌드명]: 1-2문장 설명
2. ...
3. ...

**🔬 DDS/제형 연구자 시사점**
- 주목 포인트: 1-2문장
- 실무 적용: 1-2문장
"""


def _build_user_prompt(news_data: dict[str, list[dict]]) -> str:
    blocks: list[str] = []
    for cat, items in news_data.items():
        blocks.append(f"## {cat}")
        for it in items[:25]:
            blocks.append(
                f"- title: {it.get('title', '')}\n"
                f"  source: {it.get('source', '')}\n"
                f"  date: {it.get('date', '')}\n"
                f"  link: {it.get('link', '')}\n"
                f"  desc: {it.get('desc', '')}"
            )
    return "\n".join(blocks)


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        if text.endswith("```"):
            text = text[:-3]
    return text.strip()


def summarize_for_digest(
    news_data: dict[str, list[dict]],
    api_key: str,
    model: str = DEFAULT_DIGEST_MODEL,
    max_tokens: int = 4096,
) -> dict[str, Any]:
    """Single Claude call. Returns parsed dict with trend_summary_ko + highlights.

    Retries once with stricter instructions if the first response is not
    valid JSON.
    """
    client = anthropic.Anthropic(api_key=api_key)
    user_prompt = _build_user_prompt(news_data)

    msg = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=[
            {
                "type": "text",
                "text": _SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_prompt}],
    )
    raw = msg.content[0].text
    clean = _strip_code_fence(raw)

    try:
        return json.loads(clean)
    except json.JSONDecodeError as e:
        logger.warning("digest JSON parse failed: %s; retrying once", e)
        msg2 = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=_SYSTEM_PROMPT
            + "\n\nIMPORTANT: respond with ONLY valid JSON, no code fence.",
            messages=[
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": raw},
                {
                    "role": "user",
                    "content": (
                        "Your last response was not valid JSON. "
                        "Return the same content as a single valid JSON object."
                    ),
                },
            ],
        )
        return json.loads(_strip_code_fence(msg2.content[0].text))
