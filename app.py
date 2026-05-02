"""
app.py — RxScriptor Pharma News & AI Trend Dashboard
Clinical White 테마 적용.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

import anthropic
import streamlit as st

DIGEST_PATH = Path(__file__).parent / "data" / "digest_latest.json"

from rxscriptor_header import (
    COLOR,
    apply_theme,
    section_title,
    show_footer,
    show_header,
    show_mini_header,
    tag_badges,
)
from shared_api import fetch_google_news

# ── Page config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="RxScriptor · Pharma Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme(mode="light")

NAVY   = COLOR["navy"]
RED    = COLOR["red"]
STEEL  = COLOR["steel"]
MUTED  = COLOR["muted"]
BG     = COLOR["bg"]
WHITE  = COLOR["white"]
BORDER = COLOR["border"]

CATEGORIES = {
    "🏛️ FDA / EMA": {
        "color": NAVY,
        "queries": [
            "FDA drug approval 2025",
            "EMA regulatory decision pharmaceutical",
            "FDA NDA BLA approval",
        ],
        "keywords": ["FDA", "EMA", "approval", "NDA", "BLA", "regulatory", "IND", "PDUFA"],
    },
    "💊 DDS / Formulation": {
        "color": RED,
        "queries": [
            "drug delivery nanoparticle 2025",
            "liposome lipid nanoparticle mRNA delivery",
            "PLGA polymer drug delivery",
        ],
        "keywords": [
            "nanoparticle", "liposome", "LNP", "PLGA", "DDS",
            "drug delivery", "formulation", "encapsulation", "controlled release",
        ],
    },
    "🏢 Pharma Business": {
        "color": STEEL,
        "queries": [
            "pharma merger acquisition 2025",
            "clinical trial phase 3 results",
            "pharmaceutical biotech pipeline",
        ],
        "keywords": [
            "merger", "acquisition", "M&A", "clinical trial",
            "phase 3", "biotech", "patent", "pipeline", "license",
        ],
    },
}


def collect_all_news(categories: dict, max_per_query: int = 5) -> dict:
    results: dict[str, list[dict]] = {}
    for cat_name, cat_info in categories.items():
        all_items: list[dict] = []
        seen: set[str] = set()
        for query in cat_info["queries"]:
            for item in fetch_google_news(query, max_per_query):
                if item["title"] not in seen:
                    seen.add(item["title"])
                    all_items.append(item)
        results[cat_name] = all_items
    return results


def extract_keywords(news_data: dict) -> Counter:
    all_kw: list[str] = []
    kw_list = [kw for cat in CATEGORIES.values() for kw in cat["keywords"]]
    for items in news_data.values():
        for item in items:
            text = (item["title"] + " " + item["desc"]).lower()
            for kw in kw_list:
                if kw.lower() in text:
                    all_kw.append(kw)
    return Counter(all_kw)


def generate_trend_summary(news_data: dict, api_key: str) -> str:
    headlines = [
        f"[{cat}] {item['title']}"
        for cat, items in news_data.items()
        for item in items[:4]
    ]
    prompt = f"""당신은 제약 R&D 전문 연구원입니다. DDS, CMC, PK/PD, 규제 분야 전문가입니다.

아래 오늘의 주요 제약/바이오 뉴스 헤드라인을 분석해주세요:

{chr(10).join(headlines[:30])}

다음 형식으로 한국어 트렌드 요약을 작성해주세요:

**🔥 이번 주 핵심 트렌드 (3가지)**
1. [트렌드명]: 1-2문장 설명
2. [트렌드명]: 1-2문장 설명
3. [트렌드명]: 1-2문장 설명

**🔬 DDS/제형 연구자 관점 시사점**
- 주목할 기술/규제 동향: 1-2문장
- 실무 적용 포인트: 1-2문장

**⚠️ 모니터링 필요 이슈**
1-2문장으로 요약."""

    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def summarize_article(title: str, desc: str, api_key: str) -> str:
    prompt = f"""제약 연구자 관점에서 아래 뉴스를 2-3문장으로 요약해주세요.
DDS, 규제, 임상, 비즈니스 측면 포함, 한국어로 작성.

제목: {title}
내용: {desc}"""
    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def render_news_card(item: dict, color: str, api_key: str = "", idx: int = 0) -> None:
    st.markdown(f"""
    <div style='background:{WHITE};border:1px solid {BORDER};
                border-left:3px solid {color};border-radius:8px;
                padding:16px 18px;margin-bottom:10px;
                box-shadow:0 1px 4px rgba(26,46,90,.04);'>
      <p style='margin:0 0 6px;font-size:0.85rem;font-weight:600;
                color:{NAVY};line-height:1.5;'>{item['title']}</p>
      <div style='display:flex;gap:16px;margin-bottom:6px;'>
        <span style='font-size:0.65rem;color:{MUTED};'>{item['source']}</span>
        <span style='font-size:0.65rem;color:{MUTED};'>{item['date']}</span>
      </div>
      <p style='margin:0;font-size:0.75rem;color:{MUTED};line-height:1.7;'>{item['desc']}</p>
    </div>
    """, unsafe_allow_html=True)

    col_link, col_ai = st.columns([1, 1])
    with col_link:
        st.markdown(
            f"<a href='{item['link']}' target='_blank' style='"
            f"font-size:0.68rem;color:{color};text-decoration:none;"
            f"letter-spacing:0.08em;'>원문 보기 →</a>",
            unsafe_allow_html=True,
        )
    with col_ai:
        if api_key and st.button("AI 요약", key=f"ai_{idx}_{item['title'][:15]}"):
            with st.spinner("요약 중..."):
                summary = summarize_article(item["title"], item["desc"], api_key)
            st.markdown(
                f"<div style='background:{BG};border:1px solid {BORDER};"
                f"border-radius:6px;padding:12px 14px;margin-top:8px;'>"
                f"<p style='margin:0;font-size:0.78rem;color:{NAVY};"
                f"line-height:1.8;'>{summary}</p></div>",
                unsafe_allow_html=True,
            )


def render_keyword_chart(counter: Counter) -> None:
    if not counter:
        st.info("아직 키워드가 없습니다.")
        return
    try:
        import plotly.graph_objects as go

        top_kw = counter.most_common(12)
        labels = [k for k, _ in top_kw]
        values = [v for _, v in top_kw]
        colors = [NAVY if i % 2 == 0 else RED for i in range(len(labels))]
        fig = go.Figure(go.Bar(
            x=values[::-1], y=labels[::-1],
            orientation="h",
            marker_color=colors[::-1],
            marker_line_width=0,
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=NAVY, family="DM Mono, monospace", size=12),
            margin=dict(l=0, r=20, t=10, b=10),
            height=360,
            xaxis=dict(gridcolor=BORDER, showgrid=True, zeroline=False),
            yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        for kw, cnt in counter.most_common(10):
            st.markdown(
                f"<p style='font-size:0.75rem;color:{NAVY};margin:3px 0;'>"
                f"{'█' * cnt} {kw} ({cnt})</p>",
                unsafe_allow_html=True,
            )


def load_latest_digest() -> dict | None:
    if not DIGEST_PATH.exists():
        return None
    try:
        return json.loads(DIGEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def render_latest_digest(digest: dict) -> None:
    section_title("digest", f"오늘의 다이제스트 · {digest.get('generated_at', '')[:10]}")

    trend = digest.get("trend_summary_ko") or ""
    if trend:
        st.markdown(
            f"<div style='background:{WHITE};border:1px solid {BORDER};"
            f"border-left:3px solid {NAVY};border-radius:8px;"
            f"padding:20px 24px;margin-bottom:14px;"
            f"box-shadow:0 2px 8px rgba(26,46,90,.05);'>"
            f"<p style='margin:0;font-size:0.82rem;color:{NAVY};line-height:1.9;"
            f"white-space:pre-wrap;'>{trend}</p></div>",
            unsafe_allow_html=True,
        )

    highlights = digest.get("highlights") or []
    if not highlights:
        return
    cols = st.columns(2)
    for i, h in enumerate(highlights[:8]):
        accent = RED if "DDS" in (h.get("category") or "") or "LNP" in (h.get("title") or "").upper() else NAVY
        with cols[i % 2]:
            st.markdown(
                f"<div style='background:{WHITE};border:1px solid {BORDER};"
                f"border-left:3px solid {accent};border-radius:8px;"
                f"padding:14px 16px;margin-bottom:10px;"
                f"box-shadow:0 1px 4px rgba(26,46,90,.04);'>"
                f"<p style='margin:0 0 4px;font-size:0.62rem;color:{MUTED};"
                f"letter-spacing:0.08em;text-transform:uppercase;'>"
                f"{h.get('source', '')} · {h.get('date', '')}</p>"
                f"<p style='margin:0 0 6px;font-size:0.85rem;font-weight:600;"
                f"color:{NAVY};line-height:1.4;'>{h.get('title', '')}</p>"
                f"<p style='margin:0 0 8px;font-size:0.75rem;color:{STEEL};"
                f"line-height:1.7;'>{h.get('ko_summary', '')}</p>"
                f"<a href='{h.get('link', '#')}' target='_blank' "
                f"style='font-size:0.68rem;color:{accent};text-decoration:none;"
                f"letter-spacing:0.06em;'>원문 보기 →</a>"
                f"</div>",
                unsafe_allow_html=True,
            )


# ── Sidebar ──────────────────────────────────────────────────────────
with st.sidebar:
    show_mini_header()

    st.markdown(
        f"<p style='font-size:0.68rem;letter-spacing:0.15em;color:{MUTED};"
        f"text-transform:uppercase;margin-bottom:6px;'>Claude API Key</p>",
        unsafe_allow_html=True,
    )
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "") or st.text_input(
        "API Key", type="password", placeholder="sk-ant-...", label_visibility="collapsed"
    )

    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='font-size:0.68rem;letter-spacing:0.15em;color:{MUTED};"
        f"text-transform:uppercase;margin-bottom:6px;'>Categories</p>",
        unsafe_allow_html=True,
    )
    selected_cats = [
        cat for cat in CATEGORIES
        if st.checkbox(cat, value=True, key=f"cat_{cat}")
    ]

    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='font-size:0.68rem;letter-spacing:0.15em;color:{MUTED};"
        f"text-transform:uppercase;margin-bottom:6px;'>Custom Keyword</p>",
        unsafe_allow_html=True,
    )
    custom_kw = st.text_input(
        "Custom", placeholder="e.g. GLP-1, ADC, siRNA", label_visibility="collapsed"
    )

    st.markdown("<br/>", unsafe_allow_html=True)
    fetch_btn = st.button("🔄 Fetch News", type="primary", use_container_width=True)
    trend_btn = st.button("🤖 AI 트렌드 요약", use_container_width=True) if api_key else False

# ── Main ─────────────────────────────────────────────────────────────
show_header(subtitle="Pharma News & AI Trend")

st.markdown(
    f"<p style='font-size:0.7rem;color:{MUTED};letter-spacing:0.1em;margin:-8px 0 20px;'>"
    f"🕐 {datetime.now().strftime('%Y.%m.%d  %H:%M')} KST</p>",
    unsafe_allow_html=True,
)

_latest_digest = load_latest_digest()
if _latest_digest:
    render_latest_digest(_latest_digest)
    st.markdown("<br/>", unsafe_allow_html=True)

if "news_data" not in st.session_state:
    st.session_state.news_data = {}
if "kw_counter" not in st.session_state:
    st.session_state.kw_counter = Counter()
if "trend_summary" not in st.session_state:
    st.session_state.trend_summary = ""

if fetch_btn:
    cats_to_fetch = {k: v for k, v in CATEGORIES.items() if k in selected_cats}
    if custom_kw.strip():
        cats_to_fetch[f"🔍 {custom_kw}"] = {
            "color": STEEL,
            "queries": [f"{custom_kw} pharmaceutical", f"{custom_kw} drug"],
            "keywords": custom_kw.split(),
        }
    with st.spinner("📡 뉴스 수집 중..."):
        st.session_state.news_data = collect_all_news(cats_to_fetch)
        st.session_state.kw_counter = extract_keywords(st.session_state.news_data)
    total = sum(len(v) for v in st.session_state.news_data.values())
    st.success(f"✅ 총 {total}개 뉴스 수집 완료")

if trend_btn and st.session_state.news_data:
    with st.spinner("🤖 Claude가 트렌드 분석 중..."):
        st.session_state.trend_summary = generate_trend_summary(
            st.session_state.news_data, api_key
        )

if st.session_state.news_data:
    all_news = [item for items in st.session_state.news_data.values() for item in items]

    # 메트릭
    m_cols = st.columns(4)
    metrics = [
        ("Total News", str(len(all_news)), NAVY),
        ("Categories", str(len(st.session_state.news_data)), RED),
        ("Top Keyword",
         st.session_state.kw_counter.most_common(1)[0][0]
         if st.session_state.kw_counter else "-",
         STEEL),
        ("Updated", datetime.now().strftime("%H:%M"), MUTED),
    ]
    for col, (label, value, color) in zip(m_cols, metrics):
        with col:
            st.markdown(f"""
            <div style='background:{WHITE};border:1px solid {BORDER};
                        border-top:3px solid {color};border-radius:8px;
                        padding:14px 16px;box-shadow:0 1px 4px rgba(26,46,90,.04);'>
              <p style='margin:0 0 4px;font-size:0.6rem;letter-spacing:0.18em;
                        color:{MUTED};text-transform:uppercase;'>{label}</p>
              <p style='margin:0;font-size:1.2rem;color:{NAVY};
                        font-family:"Syne",sans-serif;font-weight:700;'>{value}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    if st.session_state.trend_summary:
        section_title("ai analysis", "AI 트렌드 요약")
        st.markdown(f"""
        <div style='background:{WHITE};border:1px solid {BORDER};
                    border-left:3px solid {NAVY};border-radius:8px;
                    padding:20px 24px;margin-bottom:8px;
                    box-shadow:0 2px 8px rgba(26,46,90,.05);'>
          <p style='margin:0;font-size:0.82rem;color:{NAVY};line-height:1.9;
                    white-space:pre-wrap;'>{st.session_state.trend_summary}</p>
        </div>
        """, unsafe_allow_html=True)

    left_col, right_col = st.columns([2, 3])

    with left_col:
        section_title("trend", "Trending Keywords")
        render_keyword_chart(st.session_state.kw_counter)
        tag_badges(
            [kw for kw, _ in st.session_state.kw_counter.most_common(8)],
            color="navy",
        )

    with right_col:
        section_title("news", "Latest News")
        cat_names = list(st.session_state.news_data.keys())
        if cat_names:
            tabs = st.tabs(cat_names)
            for tab, cat_name in zip(tabs, cat_names):
                with tab:
                    items = st.session_state.news_data[cat_name]
                    color = CATEGORIES.get(cat_name, {}).get("color", NAVY)
                    for i, item in enumerate(items[:8]):
                        render_news_card(item, color, api_key, idx=i)

else:
    st.markdown(f"""
    <div style='text-align:center;padding:80px 40px;'>
      <p style='font-size:3rem;margin-bottom:16px;'>📰</p>
      <p style='font-size:1rem;color:{MUTED};margin-bottom:8px;'>
        사이드바에서 카테고리를 선택하고 <br/>
        <strong style='color:{NAVY};'>Fetch News</strong> 버튼을 클릭하세요
      </p>
      <p style='font-size:0.75rem;color:{MUTED};opacity:0.6;'>
        FDA · EMA · DDS · Pharma Business
      </p>
    </div>
    """, unsafe_allow_html=True)

show_footer()
