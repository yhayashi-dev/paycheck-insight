"""Render only committed, trusted analytics code; no simulator data enters this module."""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

_ASSET_ROOT = Path(__file__).resolve().parents[2] / "analytics"


def analytics_html() -> str:
    """Build the static loader independently of widgets, session state and URLs."""
    config = json.loads((_ASSET_ROOT / "analytics-config.json").read_text(encoding="utf-8"))
    # JSON remains data inside the script, even if future static titles contain HTML.
    serialized = json.dumps(config, ensure_ascii=True).replace("<", "\\u003c")
    script = (_ASSET_ROOT / "analytics.js").read_text(encoding="utf-8")
    if "</script" in script.lower():
        raise ValueError("Trusted analytics asset contains an unsafe script terminator")
    payload = json.dumps(f"window.SuzumeAnalyticsConfig={serialized};\n{script}", ensure_ascii=True).replace("<", "\\u003c")
    return (
        '<div hidden aria-hidden="true"></div><script>(()=>{'
        'let target=window;'
        'if(window.self!==window.top){try{'
        'const host="https://paycheck-insight-dfnvaodwxttypa7gtdouhj.streamlit.app";'
        'if(location.origin!==host||location.pathname!=="/~/+/"||window.top.location.origin!==host)return;'
        'target=window.top;'
        '}catch{return;}}'
        'const trusted=target.document.createElement("script");'
        f'trusted.textContent={payload};'
        'target.document.head.append(trusted);})();</script>'
    )


def render_analytics() -> None:
    st.html(analytics_html(), unsafe_allow_javascript=True)


def render_analytics_privacy() -> None:
    with st.expander("アクセス解析・プライバシー / Analytics privacy"):
        st.markdown(
            "2026年10月16日（日本時間）から、同意した方だけを対象に、"
            "無料のGoogle Analytics 4で閲覧ページ・閲覧時間・端末情報・大まかな流入元と、"
            "このサイトのCookieによる仮名IDを計測します。"
            "通信時にはIPアドレスがGoogleへ届きます。広告機能・Google Signalsは使いません。"
            "年収・賞与・地域などの入力、計算結果、フォーム、メール、URLの検索文字列や"
            "生の参照元URLは送りません。拒否しても試算できます。同意は解析設定から撤回できます。\n\n"
            "Googleへの通信が利用できない中国本土などの地域、通信遮断、同意拒否、広告ブロッカー等の来訪は捕捉できないことがあります。簡体字の読者がすべて中国本土にいるとも限りません。Google検索経由と中国語での閲覧は別で、記録がないことを実来訪0とは扱いません。\n\n"
            "From 16 October 2026 (Japan time), only consenting visitors are measured using "
            "free GA4: fixed page, engagement time, device, broad source category and a site cookie's "
            "pseudonymous ID. Google receives the IP address in transport. No ads or Google Signals. "
            "Salary, bonus, region, results, forms, email, query strings and raw referrer URLs are excluded. "
            "Declining does not affect calculations; consent can be withdrawn in analytics settings. "
            "Visits may not be captured where Google is unavailable, including mainland China, or when consent is declined, requests are blocked, or blockers are used. Simplified Chinese readers are not necessarily in mainland China. Google search traffic and Chinese-language readership are different; no recorded visit does not mean no actual visit."
        )
