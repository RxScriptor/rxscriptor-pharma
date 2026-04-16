"""
rxscriptor_header.py — Clinical White branded Streamlit header/chrome.

Reads colors/fonts from `rxscript-tokens.json` via `design_tokens` (both
alongside this module in the app repo).

Usage:
    from rxscriptor_header import (
        apply_theme, show_header, show_mini_header,
        section_title, info_card, tag_badges, show_footer,
    )
    apply_theme(mode="light")     # call once after st.set_page_config
    show_header(subtitle="…")
"""
from __future__ import annotations

import streamlit as st

from design_tokens import COLOR as _TOKEN_COLOR, FONT as _TOKEN_FONT

# ── Brand constants ──────────────────────────────────────────────────
BRAND = {
    "name": "RxScriptor",
    "slogan1": "From Bench. Written in Code.",
    "slogan2": "Pharmaceutical Researcher × AI Developer",
    "github": "https://github.com/rxscriptor",
}

# Backward-compatible COLOR dict (same keys the original module exposed)
COLOR = {
    "bg":      _TOKEN_COLOR["bg"],
    "bg2":     _TOKEN_COLOR["bg_alt"],
    "navy":    _TOKEN_COLOR["navy"],
    "navy_lt": _TOKEN_COLOR["navy_light"],
    "red":     _TOKEN_COLOR["red"],
    "steel":   _TOKEN_COLOR["steel"],
    "border":  _TOKEN_COLOR["border"],
    "muted":   _TOKEN_COLOR["muted"],
    "white":   _TOKEN_COLOR["surface"],
    "dark_bg": _TOKEN_COLOR["dark_bg"],
}

_GOOGLE_FONTS_URL = _TOKEN_FONT["google_url"]


# ── Global theme CSS ─────────────────────────────────────────────────
def apply_theme(mode: str = "light") -> None:
    """Apply full-app RxScriptor theming. Call once after st.set_page_config()."""
    if mode == "light":
        bg       = COLOR["bg"]
        text     = COLOR["navy"]
        sidebar  = COLOR["bg2"]
        input_bg = COLOR["white"]
    else:
        bg       = COLOR["dark_bg"]
        text     = "#F0F1F7"
        sidebar  = "#0A0E1C"
        input_bg = "#141830"

    st.markdown(f"""
    <style>
      @import url('{_GOOGLE_FONTS_URL}');

      .stApp > header {{ border-bottom: 3px solid {COLOR["navy"]}; }}
      .stApp {{ background-color: {bg}; }}

      section[data-testid="stSidebar"] {{
          background-color: {sidebar};
          border-right: 1px solid {COLOR["border"]};
      }}

      html, body, [class*="css"] {{
          color: {text};
          font-family: 'DM Mono', monospace;
      }}

      h1, h2, h3 {{
          font-family: 'Syne', sans-serif !important;
          color: {COLOR["navy"]} !important;
          letter-spacing: -0.5px !important;
      }}

      .stButton > button {{
          background: transparent;
          border: 1px solid {COLOR["navy"]};
          color: {COLOR["navy"]};
          font-family: 'DM Mono', monospace;
          font-size: 0.8rem;
          letter-spacing: 0.08em;
          border-radius: 6px;
          transition: all 0.2s;
      }}
      .stButton > button:hover {{
          background: {COLOR["navy"]};
          color: {COLOR["white"]};
      }}
      .stButton > button[kind="primary"] {{
          background: {COLOR["navy"]};
          border-color: {COLOR["navy"]};
          color: {COLOR["white"]};
          font-weight: 700;
      }}
      .stButton > button[kind="primary"]:hover {{
          background: {COLOR["red"]};
          border-color: {COLOR["red"]};
      }}

      .stTextInput > div > div > input,
      .stTextArea > div > div > textarea,
      .stSelectbox > div > div {{
          background: {input_bg};
          border: 1px solid {COLOR["border"]};
          color: {text};
          font-family: 'DM Mono', monospace;
          border-radius: 6px;
      }}
      .stTextInput > div > div > input:focus,
      .stTextArea > div > div > textarea:focus {{
          border-color: {COLOR["navy"]};
          box-shadow: 0 0 0 2px rgba(26,46,90,0.1);
      }}

      [data-testid="metric-container"] {{
          background: {COLOR["white"]};
          border: 1px solid {COLOR["border"]};
          border-top: 3px solid {COLOR["navy"]};
          border-radius: 8px;
          padding: 12px 16px;
      }}

      hr {{ border-color: {COLOR["border"]}; }}

      .stTabs [data-baseweb="tab"] {{
          font-family: 'DM Mono', monospace;
          font-size: 0.78rem;
          letter-spacing: 0.1em;
          color: {COLOR["muted"]};
      }}
      .stTabs [aria-selected="true"] {{
          color: {COLOR["navy"]} !important;
          border-bottom-color: {COLOR["red"]} !important;
      }}

      .streamlit-expanderHeader {{
          font-family: 'DM Mono', monospace;
          font-size: 0.82rem;
          color: {COLOR["navy"]};
      }}
    </style>
    """, unsafe_allow_html=True)


# ── Full-size header ─────────────────────────────────────────────────
def show_header(subtitle: str = "", show_slogan: bool = True, show_divider: bool = True) -> None:
    # NOTE: 다음 두 변수는 반드시 single-line f-string으로 유지한다.
    # 다줄 + 들여쓰기된 HTML은 st.markdown 보간 시 Markdown 코드블록으로 해석되어
    # HTML이 이스케이프돼 원문으로 렌더링되는 버그가 있다.
    subtitle_html = (
        f'<span style=\'font-family:"DM Mono",monospace;font-size:0.72rem;color:{COLOR["muted"]};letter-spacing:0.1em;margin-left:10px;\'>/ {subtitle}</span>'
        if subtitle else ""
    )

    slogan_html = (
        f'<p style=\'margin:5px 0 0 2px;font-family:"DM Mono",monospace;font-size:0.7rem;font-weight:500;letter-spacing:0.18em;color:{COLOR["navy"]};text-transform:uppercase;\'>{BRAND["slogan1"]}<span style=\'color:{COLOR["muted"]};font-weight:300;\'>&nbsp;·&nbsp;{BRAND["slogan2"]}</span></p>'
        if show_slogan else ""
    )

    st.markdown(f"""
    <div style='padding:10px 0 14px 0;border-left:3px solid {COLOR["red"]};
                padding-left:14px;margin-bottom:4px;'>
      <div style='display:flex;align-items:baseline;gap:0;line-height:1;'>
        <span style='font-family:"Syne",sans-serif;font-weight:800;
                     font-size:2rem;color:{COLOR["navy"]};letter-spacing:-1px;'>Rx</span>
        <span style='font-family:"Crimson Pro",serif;font-weight:600;font-style:italic;
                     font-size:2rem;color:{COLOR["red"]};letter-spacing:-0.5px;'>Scriptor</span>
        {subtitle_html}
      </div>
      {slogan_html}
    </div>
    """, unsafe_allow_html=True)

    if show_divider:
        st.markdown(
            f"<hr style='border:none;border-top:1px solid {COLOR['border']};margin:0 0 20px 0;'/>",
            unsafe_allow_html=True,
        )


# ── Sidebar compact header ───────────────────────────────────────────
def show_mini_header() -> None:
    st.markdown(f"""
    <div style='padding:14px 0 16px 0;text-align:center;'>
      <div style='display:flex;align-items:baseline;justify-content:center;gap:0;line-height:1;'>
        <span style='font-family:"Syne",sans-serif;font-weight:800;
                     font-size:1.5rem;color:{COLOR["navy"]};letter-spacing:-0.5px;'>Rx</span>
        <span style='font-family:"Crimson Pro",serif;font-weight:600;font-style:italic;
                     font-size:1.5rem;color:{COLOR["red"]};'>Scriptor</span>
      </div>
      <p style='margin:5px 0 0;font-family:"DM Mono",monospace;font-size:0.6rem;
                letter-spacing:0.14em;color:{COLOR["muted"]};text-transform:uppercase;'>
        From Bench. Written in Code.
      </p>
    </div>
    <hr style='border:none;border-top:1px solid {COLOR["border"]};margin:0 0 14px 0;'/>
    """, unsafe_allow_html=True)


# ── Section title ────────────────────────────────────────────────────
def section_title(label: str, title: str) -> None:
    st.markdown(f"""
    <div style='margin:28px 0 12px 0;'>
      <div style='display:flex;align-items:center;gap:10px;margin-bottom:4px;'>
        <div style='width:20px;height:2px;background:{COLOR["red"]};'></div>
        <p style='margin:0;font-family:"DM Mono",monospace;font-size:0.62rem;
                  letter-spacing:0.22em;color:{COLOR["red"]};text-transform:uppercase;'>{label}</p>
      </div>
      <h3 style='margin:0;font-family:"Syne",sans-serif;font-size:1.2rem;
                 color:{COLOR["navy"]};letter-spacing:-0.3px;'>{title}</h3>
    </div>
    """, unsafe_allow_html=True)


# ── Info card ────────────────────────────────────────────────────────
def info_card(title: str, value: str, color: str = "navy") -> None:
    c = COLOR.get(color, COLOR["navy"])
    st.markdown(f"""
    <div style='background:{COLOR["white"]};border:1px solid {COLOR["border"]};
                border-top:3px solid {c};border-radius:8px;padding:14px 18px;margin:6px 0;'>
      <p style='margin:0 0 4px;font-size:0.62rem;letter-spacing:0.18em;
                color:{COLOR["muted"]};text-transform:uppercase;
                font-family:"DM Mono",monospace;'>{title}</p>
      <p style='margin:0;font-size:1.05rem;color:{COLOR["navy"]};
                font-family:"DM Mono",monospace;font-weight:500;'>{value}</p>
    </div>
    """, unsafe_allow_html=True)


# ── Tag badges ───────────────────────────────────────────────────────
def tag_badges(tags: list, color: str = "navy") -> None:
    c = COLOR.get(color, COLOR["navy"])
    badges = "".join([
        f"<span style='display:inline-block;margin:3px 4px 3px 0;"
        f"padding:3px 12px;border-radius:4px;"
        f"border:1px solid {c}33;background:{c}0D;color:{c};"
        f"font-size:0.7rem;letter-spacing:0.08em;"
        f"font-family:\"DM Mono\",monospace;'>{tag}</span>"
        for tag in tags if tag
    ])
    st.markdown(f"<div style='margin:8px 0;'>{badges}</div>", unsafe_allow_html=True)


# ── Footer ───────────────────────────────────────────────────────────
def show_footer() -> None:
    st.markdown("<br/><br/>", unsafe_allow_html=True)
    st.markdown(
        f"<hr style='border:none;border-top:2px solid {COLOR['navy']};'/>",
        unsafe_allow_html=True,
    )
    st.markdown(f"""
    <div style='display:flex;align-items:center;justify-content:space-between;padding:10px 0;'>
      <div style='display:flex;align-items:baseline;gap:0;
                  border-left:2px solid {COLOR["red"]};padding-left:10px;'>
        <span style='font-family:"Syne",sans-serif;font-weight:800;
                     font-size:1rem;color:{COLOR["navy"]};'>Rx</span>
        <span style='font-family:"Crimson Pro",serif;font-weight:600;font-style:italic;
                     font-size:1rem;color:{COLOR["red"]};'>Scriptor</span>
      </div>
      <span style='font-family:"DM Mono",monospace;font-size:0.65rem;
                   color:{COLOR["muted"]};letter-spacing:0.12em;text-transform:uppercase;'>
        From Bench. Written in Code.
      </span>
      <a href='{BRAND["github"]}' target='_blank'
         style='font-family:"DM Mono",monospace;font-size:0.65rem;
                color:{COLOR["muted"]};text-decoration:none;letter-spacing:0.08em;'>
        github.com/rxscriptor →
      </a>
    </div>
    """, unsafe_allow_html=True)
