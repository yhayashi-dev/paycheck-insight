from __future__ import annotations

import sys
from html import escape
from pathlib import Path

import streamlit as st

# Streamlit Cloud may execute the entry point without placing the repository root first.
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.prefecture_rate_loader import get_supported_prefectures, load_rates
from src.services.simulation import simulate_annual_salary, simulate_salary_range
from src.ui.tables import (
    dataframe_to_responsive_html,
    format_results_dataframe,
    format_yen,
    parse_yen_input,
    result_to_display_rows,
    results_to_dataframe,
)


st.set_page_config(page_title="2026年 手取り試算", layout="wide")


@st.cache_data
def get_rates(prefecture_code: str = "tokyo") -> dict:
    return load_rates(prefecture_code=prefecture_code)


VERIFICATION_SECTIONS = {
    "salary_income_deduction": "給与所得控除",
    "income_tax": "所得税",
    "resident_tax": "住民税",
    "social_insurance": "社会保険料",
}

VERIFICATION_STATUS_LABELS = {
    "confirmed": "確認済み",
    "unconfirmed": "未確認",
    "pending_implementation": "計算未反映",
}


def collect_verification_items(rates: dict) -> tuple[list[dict], list[dict]]:
    """Collect display-only verification metadata from the rate file."""

    verified: list[dict] = []
    unverified: list[dict] = []
    for section_key, section_label in VERIFICATION_SECTIONS.items():
        for item in rates.get(section_key, {}).get("verification", []):
            row = {
                "section": section_label,
                "item": item["item"],
                "status": VERIFICATION_STATUS_LABELS.get(
                    item.get("status", "unconfirmed" if item["provisional"] else "confirmed"),
                    item.get("status", "未確認"),
                ),
                "applicable_period": item["applicable_period"],
                "effective_from": item.get("effective_from", "-"),
                "last_verified_on": item.get("last_verified_on", "-"),
                "source_name": item["source_name"],
                "source_url": item["source_url"],
            }
            if item["provisional"]:
                unverified.append(row)
            else:
                verified.append(row)

    return verified, unverified


def verification_cards_html(items: list[dict]) -> str:
    """Render verification metadata as responsive cards with source links."""

    if not items:
        return "<p>該当項目はありません。</p>"

    cards = []
    for item in items:
        status_class = "is-confirmed" if item["status"] == "確認済み" else "is-pending"
        source_url = item["source_url"]
        if source_url:
            source = (
                f'<a href="{escape(source_url)}" target="_blank" rel="noopener noreferrer">'
                f'{escape(item["source_name"])}</a>'
            )
        else:
            source = escape(item["source_name"])

        cards.append(
            '<article class="verification-card">'
            '<div class="verification-card-header">'
            f'<span class="verification-card-section">{escape(item["section"])}</span>'
            f'<strong class="verification-card-item">{escape(item["item"])}</strong>'
            f'<span class="verification-card-status {status_class}">{escape(item["status"])}</span>'
            "</div>"
            '<dl class="verification-card-fields">'
            '<div class="verification-card-field">'
            '<dt>適用年度・条件</dt>'
            f'<dd>{escape(item["applicable_period"])}</dd>'
            "</div>"
            '<div class="verification-card-field">'
            '<dt>適用開始日</dt>'
            f'<dd>{escape(item["effective_from"])}</dd>'
            "</div>"
            '<div class="verification-card-field">'
            '<dt>最終確認日</dt>'
            f'<dd>{escape(item["last_verified_on"])}</dd>'
            "</div>"
            '<div class="verification-card-field">'
            '<dt>出典</dt>'
            f"<dd>{source}</dd>"
            "</div>"
            "</dl>"
            "</article>"
        )

    return (
        f'<div class="verification-card-list">{"".join(cards)}</div>'
    )

st.markdown(
    """
    <style>
    .block-container {
        max-width: 1320px;
        padding: 1.35rem 0.75rem 2rem;
    }
    .app-title {
        color: rgb(49, 51, 63);
        font-size: clamp(1.35rem, 1.9vw, 1.9rem) !important;
        font-weight: 700 !important;
        line-height: 1.18 !important;
        margin: 0 0 0.28rem !important;
        letter-spacing: 0 !important;
        max-width: 36em;
    }
    .app-subtitle {
        color: rgba(49, 51, 63, 0.78);
        font-size: 0.95rem !important;
        line-height: 1.4 !important;
        margin: 0 0 0.65rem !important;
    }
    .app-caption {
        color: rgba(49, 51, 63, 0.72);
        font-size: clamp(0.78rem, 0.95vw, 0.9rem) !important;
        line-height: 1.4 !important;
        margin: 0 0 0.45rem !important;
        max-width: 68em;
    }
    .compact-warning {
        background: rgb(255, 246, 214);
        border: 1px solid rgba(217, 160, 0, 0.28);
        border-radius: 8px;
        color: rgb(92, 64, 0);
        font-size: 0.82rem;
        line-height: 1.35;
        margin: 0 0 0.45rem;
        padding: 0.42rem 0.6rem;
    }
    .verification-card-list {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 0.75rem;
        margin: 0.35rem 0 0.8rem;
    }
    .verification-card {
        background: white;
        border: 1px solid rgba(49, 51, 63, 0.16);
        border-radius: 8px;
        min-width: 0;
        overflow: hidden;
    }
    .verification-card-header {
        display: grid;
        gap: 0.25rem;
        padding: 0.7rem 0.75rem;
        background: rgba(240, 242, 246, 0.7);
    }
    .verification-card-section {
        color: rgba(49, 51, 63, 0.64);
        font-size: 0.75rem;
        font-weight: 700;
    }
    .verification-card-item {
        color: rgb(49, 51, 63);
        font-size: 0.95rem;
        line-height: 1.4;
        overflow-wrap: anywhere;
    }
    .verification-card-status {
        font-size: 0.8rem;
        font-weight: 700;
    }
    .verification-card-status.is-confirmed {
        color: rgb(0, 104, 89);
    }
    .verification-card-status.is-pending {
        color: rgb(146, 92, 0);
    }
    .verification-card-fields {
        margin: 0;
        padding: 0 0.75rem;
    }
    .verification-card-field {
        border-bottom: 1px solid rgba(49, 51, 63, 0.1);
        padding: 0.6rem 0;
    }
    .verification-card-field:last-child {
        border-bottom: 0;
    }
    .verification-card-field dt {
        color: rgba(49, 51, 63, 0.64);
        font-size: 0.75rem;
        font-weight: 700;
        margin-bottom: 0.18rem;
    }
    .verification-card-field dd {
        color: rgb(49, 51, 63);
        font-size: 0.84rem;
        line-height: 1.45;
        margin: 0;
        overflow-wrap: anywhere;
    }
    [data-testid="stTextInput"] {
        margin-bottom: 0.35rem;
    }
    [data-testid="stMarkdownContainer"] h3 {
        margin-top: 0.55rem;
        margin-bottom: 0.45rem;
        font-size: 1.25rem;
    }
    .summary-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.75rem;
        margin: 0.6rem 0 1rem;
    }
    .summary-card {
        border: 1px solid rgba(49, 51, 63, 0.18);
        border-radius: 8px;
        padding: 0.9rem 1rem;
        background: rgba(250, 250, 250, 0.78);
        min-width: 0;
    }
    .summary-label {
        color: rgba(49, 51, 63, 0.72);
        font-size: 0.88rem;
        line-height: 1.25;
        margin-bottom: 0.35rem;
        white-space: nowrap;
    }
    .summary-value {
        color: rgb(49, 51, 63);
        font-size: clamp(1.05rem, 1.5vw, 1.55rem);
        font-weight: 700;
        line-height: 1.25;
        white-space: normal;
        overflow-wrap: anywhere;
        letter-spacing: 0;
    }
    [data-testid="stDataFrame"] {
        width: 100%;
        max-width: 100%;
    }
    .responsive-table-wrap {
        width: 100%;
        max-width: 100%;
        overflow-x: auto;
        border: 1px solid rgba(49, 51, 63, 0.16);
        border-radius: 8px;
    }
    .responsive-table {
        width: max-content;
        min-width: 100%;
        border-collapse: collapse;
        font-size: 0.88rem;
        line-height: 1.35;
    }
    .responsive-table th,
    .responsive-table td {
        border-bottom: 1px solid rgba(49, 51, 63, 0.12);
        padding: 0.55rem 0.65rem;
        text-align: right;
        white-space: nowrap;
    }
    .responsive-table th {
        background: rgba(240, 242, 246, 0.75);
        color: rgba(49, 51, 63, 0.86);
        font-weight: 700;
    }
    .responsive-table th:first-child,
    .responsive-table td:first-child {
        text-align: left;
        font-weight: 700;
    }
    .responsive-table tr:last-child td {
        border-bottom: 0;
    }
    .range-mobile-list {
        display: none;
    }
    @media (max-width: 900px) {
        .summary-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
    }
    @media (max-width: 520px) {
        .block-container {
            padding: 1rem 0.75rem 1.5rem;
        }
        .app-title {
            font-size: 1.35rem !important;
            line-height: 1.22;
        }
        .app-caption {
            font-size: 0.82rem !important;
            line-height: 1.45 !important;
        }
        .compact-warning {
            padding: 0.4rem 0.55rem;
        }
        .verification-card-list {
            grid-template-columns: minmax(0, 1fr);
            gap: 0.65rem;
        }
        .summary-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.5rem;
        }
        .summary-card {
            padding: 0.75rem;
        }
        .summary-label {
            white-space: normal;
        }
        .summary-value {
            font-size: 1rem;
        }
        .responsive-table-wrap {
            overflow-x: visible;
            border: 0;
        }
        .responsive-table {
            display: none;
        }
        .range-mobile-list {
            display: block;
        }
        .range-mobile-card {
            border: 1px solid rgba(49, 51, 63, 0.16);
            border-radius: 8px;
            margin-bottom: 0.75rem;
            overflow: hidden;
            background: white;
        }
        .range-mobile-main-row,
        .range-mobile-detail-row {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            border-bottom: 1px solid rgba(49, 51, 63, 0.10);
            padding: 0.55rem 0.65rem;
            white-space: normal;
            overflow-wrap: anywhere;
        }
        .range-mobile-main-row span,
        .range-mobile-detail-row span {
            color: rgba(49, 51, 63, 0.72);
            font-weight: 700;
            text-align: left;
            flex: 0 0 42%;
        }
        .range-mobile-main-row strong,
        .range-mobile-detail-row strong {
            color: rgb(49, 51, 63);
            font-weight: 700;
            text-align: right;
        }
        .range-mobile-main-row:first-child {
            background: rgba(240, 242, 246, 0.75);
        }
        .range-mobile-details {
            border-top: 1px solid rgba(49, 51, 63, 0.08);
        }
        .range-mobile-details summary {
            cursor: pointer;
            padding: 0.55rem 0.65rem;
            color: rgb(0, 104, 201);
            font-weight: 700;
            list-style-position: inside;
        }
        .range-mobile-details .range-mobile-detail-row:last-child {
            border-bottom: 0;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <h1 class="app-title">2026年 手取り試算</h1>
    <p class="app-subtitle">会社員向け 税・社会保険料・手取りの概算</p>
    """,
    unsafe_allow_html=True,
)

prefecture_configs = get_supported_prefectures()
prefecture_names = {config.code: config.display_name for config in prefecture_configs}
selected_prefecture_code = st.selectbox(
    "都道府県",
    options=[config.code for config in prefecture_configs],
    format_func=prefecture_names.__getitem__,
)

rates = get_rates(selected_prefecture_code)
metadata = rates["metadata"]

st.markdown(
    f'<p class="app-caption">{escape(metadata["prefecture"])}・52歳・単身・扶養なし・会社員・'
    '協会けんぽ・給与収入のみ・賞与なし・12か月均等支給の概算です。</p>',
    unsafe_allow_html=True,
)

if metadata["provisional"]:
    st.markdown(
        f'<div class="compact-warning">{escape(metadata["notice"])}</div>',
        unsafe_allow_html=True,
    )

verified_items, unverified_items = collect_verification_items(rates)
with st.expander("確認状況と出典"):
    st.markdown(
        f"一部未確認項目あり。確認済み {len(verified_items)} 件、未確認 {len(unverified_items)} 件です。"
    )
    st.markdown("#### 確認済み項目")
    st.markdown(verification_cards_html(verified_items), unsafe_allow_html=True)
    st.markdown("#### 未確認項目")
    st.markdown(verification_cards_html(unverified_items), unsafe_allow_html=True)

annual_salary_text = st.text_input(
    "年収",
    value=format_yen(5_000_000),
    help="3桁カンマ付きで入力できます。例: 5,000,000円",
)

try:
    annual_salary = parse_yen_input(annual_salary_text)
except ValueError:
    st.error("年収は 5,000,000円 のように数字、カンマ、円で入力してください。")
    st.stop()

result = simulate_annual_salary(int(annual_salary), rates)

st.subheader("試算結果")

summary_items = [
    ("年間手取り", format_yen(result.annual_take_home)),
    ("月平均手取り", format_yen(result.monthly_take_home_average)),
    ("会社負担分", format_yen(result.insurance.employer_total)),
    ("総人件費", format_yen(result.total_labor_cost)),
]
summary_html = '<div class="summary-grid">'
for label, value in summary_items:
    summary_html += (
        '<div class="summary-card">'
        f'<div class="summary-label">{label}</div>'
        f'<div class="summary-value">{value}</div>'
        "</div>"
    )
summary_html += "</div>"
st.markdown(summary_html, unsafe_allow_html=True)

st.table(result_to_display_rows(result))

with st.expander("計算前提"):
    st.write(
        {
            "対象年": metadata["year"],
            "地域": metadata["prefecture"],
            "年齢": metadata["age"],
            "世帯": metadata["household"],
            "扶養人数": metadata["dependents"],
            "保険者": metadata["health_insurer"],
            "賞与": "なし",
            "健康保険 標準報酬月額": f"{result.insurance.health_standard_monthly:,.0f}円",
            "厚生年金 標準報酬月額": f"{result.insurance.pension_standard_monthly:,.0f}円",
            "所得税 課税所得": f"{result.tax.taxable_income_for_income_tax:,.0f}円",
            "住民税 課税所得": f"{result.tax.taxable_income_for_resident_tax:,.0f}円",
        }
    )

st.subheader("年収別一覧")
range_results = simulate_salary_range(rates)
df = results_to_dataframe(range_results)
display_df = format_results_dataframe(df)

st.markdown(dataframe_to_responsive_html(display_df), unsafe_allow_html=True)
