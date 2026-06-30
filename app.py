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


UI_TEXT = {
    "ja": {
        "title": "2026年 手取り試算",
        "subtitle": "会社員向け 税・社会保険料・手取りの概算",
        "prefecture": "都道府県",
        "annual_salary": "年収",
        "results": "試算結果",
        "annual_take_home": "年間手取り",
        "monthly_take_home": "月平均手取り",
        "employer_burden": "会社負担分",
        "total_labor_cost": "総人件費",
        "social_insurance_total": "社会保険料合計",
        "tax_total": "税金合計",
        "verification_status_sources": "確認状況と出典",
        "salary_examples": "年収別一覧",
        "prefecture_comparison": "地域比較",
    },
    "en": {
        "title": "2026 Take-home Pay Simulator",
        "subtitle": "Estimate taxes, social insurance, and take-home pay for employees in Japan",
        "prefecture": "Prefecture",
        "annual_salary": "Annual salary",
        "results": "Results",
        "annual_take_home": "Annual take-home pay",
        "monthly_take_home": "Monthly average take-home pay",
        "employer_burden": "Employer burden",
        "total_labor_cost": "Total labor cost",
        "social_insurance_total": "Total social insurance",
        "tax_total": "Total taxes",
        "verification_status_sources": "Verification status and sources",
        "salary_examples": "Salary examples",
        "prefecture_comparison": "Prefecture comparison",
    },
}

ENGLISH_WARNING_MESSAGE = (
    "Some items are still unverified. Income tax, resident tax, salary income deductions, "
    "and major social insurance rates are based on official sources. Final rounding rules "
    "for income tax, the child and family support contribution, and some local tax rounding "
    "rules are shown as unverified."
)

ENGLISH_PARTIAL_TRANSLATION_NOTE = (
    "Some official terms and source titles are currently shown in Japanese. "
    "This English mode is partially translated and intended as a first step "
    "for non-Japanese users."
)

ENGLISH_PREFECTURE_NAMES = {
    "tokyo": "Tokyo",
    "osaka": "Osaka",
    "kanagawa": "Kanagawa (Yokohama assumed)",
}

SALARY_EXAMPLE_LABELS = {
    "ja": {
        "年収": "年収",
        "月額給与": "月額給与",
        "所得税": "所得税",
        "住民税": "住民税",
        "健康保険": "健康保険",
        "介護保険": "介護保険",
        "厚生年金": "厚生年金",
        "雇用保険": "雇用保険",
        "社会保険料合計": "社会保険料合計",
        "税金合計": "税金合計",
        "年間手取り": "年間手取り",
        "月平均手取り": "月平均手取り",
        "会社負担分": "会社負担分",
        "総人件費": "総人件費",
        "手取り率": "手取り率",
    },
    "en": {
        "年収": "Annual salary",
        "月額給与": "Monthly salary",
        "所得税": "Income tax",
        "住民税": "Resident tax",
        "健康保険": "Health insurance",
        "介護保険": "Long-term care insurance",
        "厚生年金": "Employees' pension",
        "雇用保険": "Employment insurance",
        "社会保険料合計": "Total social insurance",
        "税金合計": "Total taxes",
        "年間手取り": "Annual take-home pay",
        "月平均手取り": "Monthly average take-home pay",
        "会社負担分": "Employer burden",
        "総人件費": "Total labor cost",
        "手取り率": "Take-home rate",
    },
}

SALARY_EXAMPLE_DETAIL_LABELS = {
    "ja": ("詳細を表示", "詳細を閉じる"),
    "en": ("Show details", "Hide details"),
}

RESULT_BREAKDOWN_LABELS = {
    "ja": {
        "item_column": "項目",
        "amount_column": "金額",
        "所得税": "所得税",
        "住民税": "住民税",
        "健康保険": "健康保険",
        "介護保険": "介護保険",
        "厚生年金": "厚生年金",
        "雇用保険": "雇用保険",
        "社会保険料合計": "社会保険料合計",
        "税金合計": "税金合計",
        "年間手取り": "年間手取り",
        "月平均手取り": "月平均手取り",
        "会社負担分": "会社負担分",
        "総人件費": "総人件費",
    },
    "en": {
        "item_column": "Item",
        "amount_column": "Amount",
        "所得税": "Income tax",
        "住民税": "Resident tax",
        "健康保険": "Health insurance",
        "介護保険": "Long-term care insurance",
        "厚生年金": "Employees’ pension",
        "雇用保険": "Employment insurance",
        "社会保険料合計": "Total social insurance",
        "税金合計": "Total taxes",
        "年間手取り": "Annual take-home pay",
        "月平均手取り": "Monthly average take-home pay",
        "会社負担分": "Employer burden",
        "総人件費": "Total labor cost",
    },
}

VERIFICATION_DISPLAY_TEXT = {
    "ja": {
        "verified_items": "確認済み項目",
        "unverified_items": "未確認項目",
        "category": "分類",
        "item": "項目",
        "status": "状態",
        "verified": "確認済み",
        "unverified": "未確認",
        "pending_implementation": "計算未反映",
        "applicable_period": "適用年度・条件",
        "effective_date": "適用開始日",
        "last_verified_date": "最終確認日",
        "source": "出典",
        "empty": "該当項目はありません。",
    },
    "en": {
        "verified_items": "Verified items",
        "unverified_items": "Unverified items",
        "category": "Category",
        "item": "Item",
        "status": "Status",
        "verified": "Verified",
        "unverified": "Unverified",
        "pending_implementation": "Not reflected in calculation",
        "applicable_period": "Applicable year / conditions",
        "effective_date": "Effective date",
        "last_verified_date": "Last verified date",
        "source": "Source",
        "empty": "No items.",
    },
}

VERIFICATION_ITEM_ENGLISH_ALIASES = {
    "介護保険料率": "Long-term care insurance rate",
    "住民税の基礎控除": "Resident tax basic deduction",
    "健康保険料率": "Health insurance rate",
    "前年所得課税": "Taxation based on prior-year income",
    "厚生年金保険料率": "Employees’ pension insurance rate",
    "均等割": "Per capita levy",
    "子ども・子育て拠出金率": "Child and childcare contribution rate",
    "子ども・子育て支援金率（計算未反映）": (
        "Child and family support contribution rate (not reflected in calculation)"
    ),
    "市民税・府民税の個別100円未満切捨て（計算未反映）": (
        "Separate rounding down below JPY 100 for municipal and prefectural resident tax "
        "(not reflected in calculation)"
    ),
    "市民税・県民税の個別100円未満切捨て（計算未反映）": (
        "Separate rounding down below JPY 100 for municipal and prefectural resident tax "
        "(not reflected in calculation)"
    ),
    "復興特別所得税率": "Special income tax for reconstruction rate",
    "所得割の税率": "Income-based resident tax rate",
    "所得税の基礎控除": "Income tax basic deduction",
    "所得税の速算表": "Income tax rate table",
    "所得税額の最終端数処理": "Final rounding of income tax amount",
    "森林環境税": "Forest environment tax",
    "標準報酬月額": "Standard monthly remuneration",
    "水源環境保全税": "Water source environment conservation tax",
    "社会保険料控除": "Social insurance premium deduction",
    "税額の100円未満切捨て": "Rounding down tax amount below JPY 100",
    "給与所得控除": "Employment income deduction",
    "給与所得控除の最低保障額": "Minimum guaranteed employment income deduction",
    "課税所得の1,000円未満切捨て": "Rounding down taxable income below JPY 1,000",
    "課税標準の1,000円未満切捨て": "Rounding down resident tax base below JPY 1,000",
    "調整控除": "Adjustment deduction",
    "雇用保険料率": "Employment insurance rate",
    "非課税判定（大阪市）": "Tax-exempt eligibility (Osaka City)",
    "非課税判定（東京23区）": "Tax-exempt eligibility (Tokyo 23 wards)",
    "非課税判定（横浜市）": "Tax-exempt eligibility (Yokohama City)",
}


def ui_text(language: str, key: str) -> str:
    """Return a UI label while keeping Japanese as the default language."""

    return UI_TEXT.get(language, UI_TEXT["ja"])[key]


def currency_unit(language: str) -> str:
    """Return the display-only currency unit for the selected language."""

    return "JPY" if language == "en" else "円"


def format_display_currency(value: int, unit: str) -> str:
    """Localize the stable one-argument yen formatter for hot-reload compatibility."""

    yen_text = format_yen(value)
    if unit == "円":
        return yen_text
    numeric_text = yen_text[:-1] if yen_text.endswith("円") else yen_text
    return f"{numeric_text} {unit}"


def parse_currency_input(value: str) -> int:
    """Normalize the English display unit before using the stable yen parser."""

    return parse_yen_input(value.upper().replace("JPY", "円"))


def localize_yen_text(value: object, unit: str) -> object:
    """Convert already-formatted yen text without changing its numeric value."""

    if unit == "円" or not isinstance(value, str) or not value.endswith("円"):
        return value
    return f"{value[:-1]} {unit}"


def localized_result_rows(
    result: object,
    unit: str,
    language: str = "ja",
) -> list[dict[str, str]]:
    """Localize result rows while calling the imported helper with its stable API."""

    rows = result_to_display_rows(result)
    labels = RESULT_BREAKDOWN_LABELS.get(language, RESULT_BREAKDOWN_LABELS["ja"])
    return [
        {
            labels["item_column"]: labels.get(row["項目"], row["項目"]),
            labels["amount_column"]: str(localize_yen_text(row["金額"], unit)),
        }
        for row in rows
    ]


def localized_results_dataframe(df: object, unit: str) -> object:
    """Localize a formatted salary table without passing new args to cached helpers."""

    formatted = format_results_dataframe(df)
    if unit == "円":
        return formatted
    for column in formatted.columns:
        formatted[column] = formatted[column].map(
            lambda value: localize_yen_text(value, unit)
        )
    return formatted


def warning_message(language: str, metadata: dict) -> str:
    """Use the existing regional notice in Japanese and a shared English notice."""

    if language == "en":
        return ENGLISH_WARNING_MESSAGE
    return metadata["notice"]


def partial_translation_note(language: str) -> str | None:
    """Return the English-only note about the current translation scope."""

    if language == "en":
        return ENGLISH_PARTIAL_TRANSLATION_NOTE
    return None


def prefecture_display_name(language: str, prefecture_code: str, japanese_name: str) -> str:
    """Translate a prefecture label without changing its internal selection code."""

    if language == "en":
        return ENGLISH_PREFECTURE_NAMES[prefecture_code]
    return japanese_name


def assumption_summary(language: str, prefecture_code: str, metadata: dict) -> str:
    """Describe the fixed simulation assumptions in the selected UI language."""

    if language == "en":
        prefecture_name = ENGLISH_PREFECTURE_NAMES[prefecture_code]
        return (
            f"{prefecture_name} · Age {metadata['age']} · Single · No dependents · Employee · "
            "Japan Health Insurance Association · Salary income only · No bonus · "
            "Paid evenly over 12 months."
        )
    return (
        f"{metadata['prefecture']}・{metadata['age']}歳・単身・扶養なし・会社員・"
        "協会けんぽ・給与収入のみ・賞与なし・12か月均等支給の概算です。"
    )


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

DEFAULT_ANNUAL_SALARY = 5_000_000
MIN_ANNUAL_SALARY = 1_000_000
MAX_ANNUAL_SALARY = 20_000_000
ANNUAL_SALARY_STEP = 100_000
PREFECTURE_COMPARISON_METRICS = (
    ("annual_take_home", lambda result: result.annual_take_home),
    ("monthly_take_home", lambda result: result.monthly_take_home_average),
    ("social_insurance_total", lambda result: result.insurance.employee_total),
    ("tax_total", lambda result: result.tax.total),
    ("employer_burden", lambda result: result.insurance.employer_total),
    ("total_labor_cost", lambda result: result.total_labor_cost),
)


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


def verification_summary_text(language: str, verified_count: int, unverified_count: int) -> str:
    """Format verification counts in the selected display language."""

    if language == "en":
        return (
            "Some items are still unverified. "
            f"Verified: {verified_count}, Unverified: {unverified_count}."
        )
    return (
        f"一部未確認項目あり。確認済み {verified_count} 件、"
        f"未確認 {unverified_count} 件です。"
    )


def verification_item_display_name(item_name: str, language: str) -> str:
    """Append a trusted English alias while preserving the official Japanese item name."""

    if language != "en":
        return item_name
    english_alias = VERIFICATION_ITEM_ENGLISH_ALIASES.get(item_name)
    if not english_alias:
        return item_name
    return f"{item_name} / {english_alias}"


def verification_cards_html(items: list[dict], language: str = "ja") -> str:
    """Render verification metadata as responsive cards with source links."""

    labels = VERIFICATION_DISPLAY_TEXT.get(language, VERIFICATION_DISPLAY_TEXT["ja"])
    if not items:
        return f'<p>{escape(labels["empty"])}</p>'

    cards = []
    for item in items:
        displayed_item_name = verification_item_display_name(item["item"], language)
        status_class = "is-confirmed" if item["status"] == "確認済み" else "is-pending"
        status_key = {
            "確認済み": "verified",
            "未確認": "unverified",
            "計算未反映": "pending_implementation",
        }.get(item["status"], "unverified")
        displayed_status = labels[status_key]
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
            '<div class="verification-card-header-field">'
            f'<span class="verification-card-label">{escape(labels["category"])}</span>'
            f'<span class="verification-card-section">{escape(item["section"])}</span>'
            "</div>"
            '<div class="verification-card-header-field">'
            f'<span class="verification-card-label">{escape(labels["item"])}</span>'
            f'<strong class="verification-card-item">{escape(displayed_item_name)}</strong>'
            "</div>"
            '<div class="verification-card-header-field">'
            f'<span class="verification-card-label">{escape(labels["status"])}</span>'
            f'<span class="verification-card-status {status_class}">{escape(displayed_status)}</span>'
            "</div>"
            "</div>"
            '<dl class="verification-card-fields">'
            '<div class="verification-card-field">'
            f'<dt>{escape(labels["applicable_period"])}</dt>'
            f'<dd>{escape(item["applicable_period"])}</dd>'
            "</div>"
            '<div class="verification-card-field">'
            f'<dt>{escape(labels["effective_date"])}</dt>'
            f'<dd>{escape(item["effective_from"])}</dd>'
            "</div>"
            '<div class="verification-card-field">'
            f'<dt>{escape(labels["last_verified_date"])}</dt>'
            f'<dd>{escape(item["last_verified_on"])}</dd>'
            "</div>"
            '<div class="verification-card-field">'
            f'<dt>{escape(labels["source"])}</dt>'
            f"<dd>{source}</dd>"
            "</div>"
            "</dl>"
            "</article>"
        )

    return (
        f'<div class="verification-card-list">{"".join(cards)}</div>'
    )


def format_signed_yen(value: int, language: str = "ja") -> str:
    """Format a comparison difference with an explicit sign."""

    unit = currency_unit(language)
    separator = "" if unit == "円" else " "
    return f"{value:+,}{separator}{unit}"


def annual_salary_input_label(language: str) -> str:
    """Show the localized currency unit alongside the editable salary input."""

    if language == "en":
        return "Annual salary (JPY)"
    return "年収（円）"


def comparison_assumption_summary(
    language: str,
    annual_salary: int = DEFAULT_ANNUAL_SALARY,
) -> str:
    """Describe the inputs used for the prefecture comparison."""

    if language == "en":
        return (
            f"Annual salary {format_display_currency(annual_salary, currency_unit(language))} · "
            "Age 52 · Single · "
            "No dependents · No bonus · Paid evenly over 12 months."
        )
    return (
        f"年収 {format_yen(annual_salary)}・52歳・単身・扶養なし・"
        "賞与なし・12か月均等支給で比較しています。"
    )


def prefecture_comparison_html(
    prefecture_results: list[tuple[str, object]] | object,
    legacy_osaka_result: object | None = None,
    language: str = "ja",
) -> str:
    """Render fixed-salary prefecture results and differences from the first item."""

    if legacy_osaka_result is not None:
        legacy_names = (
            ("Tokyo", "Osaka")
            if language == "en"
            else ("東京都", "大阪府")
        )
        prefecture_results = [
            (legacy_names[0], prefecture_results),
            (legacy_names[1], legacy_osaka_result),
        ]
    if not isinstance(prefecture_results, list):
        raise TypeError("prefecture_results must be a list of name and result pairs.")
    if len(prefecture_results) < 2:
        raise ValueError("Prefecture comparison requires at least two results.")

    prefecture_cards = []
    unit = currency_unit(language)
    for prefecture_name, comparison_result in prefecture_results:
        metric_rows = []
        for label_key, getter in PREFECTURE_COMPARISON_METRICS:
            metric_rows.append(
                '<div class="comparison-metric-row">'
                f'<dt>{escape(ui_text(language, label_key))}</dt>'
                f'<dd>{format_display_currency(getter(comparison_result), unit)}</dd>'
                "</div>"
            )
        prefecture_cards.append(
            '<article class="comparison-prefecture-card">'
            f'<h4>{escape(prefecture_name)}</h4>'
            f'<dl>{"".join(metric_rows)}</dl>'
            "</article>"
        )

    reference_name, reference_result = prefecture_results[0]
    difference_sections = []
    for prefecture_name, comparison_result in prefecture_results[1:]:
        difference_rows = []
        for label_key, getter in PREFECTURE_COMPARISON_METRICS:
            difference = getter(comparison_result) - getter(reference_result)
            if language == "en":
                difference_copy = (
                    f"{escape(prefecture_name)} compared with {escape(reference_name)}: "
                )
            else:
                difference_copy = (
                    f"{escape(prefecture_name)}は{escape(reference_name)}より "
                )
            difference_rows.append(
                '<div class="comparison-difference-row">'
                f'<span>{escape(ui_text(language, label_key))}</span>'
                '<strong>'
                f'{difference_copy}'
                f'<span class="comparison-difference-value">{format_signed_yen(difference, language)}</span>'
                "</strong>"
                "</div>"
            )
        if language == "en":
            difference_title = (
                f"Difference ({escape(prefecture_name)} - {escape(reference_name)})"
            )
        else:
            difference_title = (
                f"差額（{escape(prefecture_name)} − {escape(reference_name)}）"
            )
        difference_sections.append(
            '<h4 class="comparison-difference-title">'
            f'{difference_title}'
            "</h4>"
            f'<div class="comparison-difference-list">{"".join(difference_rows)}</div>'
        )

    return (
        f'<div class="comparison-prefecture-grid">{"".join(prefecture_cards)}</div>'
        f'{"".join(difference_sections)}'
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
    .translation-note {
        background: rgb(241, 247, 252);
        border: 1px solid rgba(44, 95, 132, 0.2);
        border-radius: 8px;
        color: rgb(48, 72, 89);
        font-size: 0.82rem;
        line-height: 1.4;
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
    .verification-card-header-field {
        display: grid;
        gap: 0.14rem;
    }
    .verification-card-label {
        color: rgba(49, 51, 63, 0.58);
        font-size: 0.7rem;
        font-weight: 700;
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
    .comparison-prefecture-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 0.75rem;
        margin: 0.55rem 0 0.9rem;
    }
    .comparison-prefecture-card {
        background: white;
        border: 1px solid rgba(49, 51, 63, 0.16);
        border-radius: 8px;
        min-width: 0;
        overflow: hidden;
    }
    .comparison-prefecture-card h4 {
        background: rgba(240, 242, 246, 0.75);
        color: rgb(49, 51, 63);
        font-size: 1rem;
        margin: 0;
        padding: 0.7rem 0.8rem;
    }
    .comparison-prefecture-card dl {
        margin: 0;
        padding: 0 0.8rem;
    }
    .comparison-metric-row,
    .comparison-difference-row {
        align-items: baseline;
        border-bottom: 1px solid rgba(49, 51, 63, 0.1);
        display: flex;
        gap: 0.75rem;
        justify-content: space-between;
        padding: 0.55rem 0;
    }
    .comparison-metric-row:last-child,
    .comparison-difference-row:last-child {
        border-bottom: 0;
    }
    .comparison-metric-row dt,
    .comparison-difference-row span:first-child {
        color: rgba(49, 51, 63, 0.68);
        font-size: 0.84rem;
        font-weight: 700;
    }
    .comparison-metric-row dd,
    .comparison-difference-row strong {
        color: rgb(49, 51, 63);
        font-size: 0.9rem;
        font-weight: 700;
        margin: 0;
        text-align: right;
    }
    .comparison-difference-title {
        color: rgb(49, 51, 63);
        font-size: 0.95rem;
        margin: 0.25rem 0 0.35rem;
    }
    .comparison-difference-list {
        border-bottom: 1px solid rgba(49, 51, 63, 0.16);
        border-top: 1px solid rgba(49, 51, 63, 0.16);
        margin-bottom: 1rem;
    }
    .comparison-difference-value {
        white-space: nowrap;
    }
    [data-testid="stDataFrame"] {
        width: 100%;
        max-width: 100%;
    }
    .range-mobile-list {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 0.75rem;
    }
    .range-mobile-card {
        border: 1px solid rgba(49, 51, 63, 0.16);
        border-radius: 8px;
        min-width: 0;
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
    .range-details-hide {
        display: none;
    }
    .range-mobile-details[open] .range-details-show {
        display: none;
    }
    .range-mobile-details[open] .range-details-hide {
        display: inline;
    }
    .range-mobile-details .range-mobile-detail-row:last-child {
        border-bottom: 0;
    }
    @media (max-width: 900px) {
        .summary-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
    }
    @media (max-width: 760px) {
        .range-mobile-list {
            grid-template-columns: minmax(0, 1fr);
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
        .comparison-prefecture-grid {
            grid-template-columns: minmax(0, 1fr);
            gap: 0.65rem;
        }
        .comparison-metric-row,
        .comparison-difference-row {
            align-items: flex-start;
        }
        .comparison-metric-row dt,
        .comparison-difference-row span:first-child {
            flex: 0 0 42%;
        }
        .comparison-metric-row dd,
        .comparison-difference-row strong {
            overflow-wrap: anywhere;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

language_names = {"ja": "日本語", "en": "English"}
selected_language = st.selectbox(
    "表示言語 / Language",
    options=list(language_names),
    format_func=language_names.__getitem__,
)
selected_currency_unit = currency_unit(selected_language)

st.markdown(
    f"""
    <h1 class="app-title">{escape(ui_text(selected_language, "title"))}</h1>
    <p class="app-subtitle">{escape(ui_text(selected_language, "subtitle"))}</p>
    """,
    unsafe_allow_html=True,
)

prefecture_configs = get_supported_prefectures()
prefecture_names = {
    config.code: prefecture_display_name(
        selected_language,
        config.code,
        config.display_name,
    )
    for config in prefecture_configs
}
selected_prefecture_code = st.selectbox(
    ui_text(selected_language, "prefecture"),
    options=[config.code for config in prefecture_configs],
    format_func=prefecture_names.__getitem__,
)

rates = get_rates(selected_prefecture_code)
metadata = rates["metadata"]

st.markdown(
    f'<p class="app-caption">{escape(assumption_summary(selected_language, selected_prefecture_code, metadata))}</p>',
    unsafe_allow_html=True,
)

if metadata["provisional"]:
    st.markdown(
        f'<div class="compact-warning">{escape(warning_message(selected_language, metadata))}</div>',
        unsafe_allow_html=True,
    )

translation_note = partial_translation_note(selected_language)
if translation_note:
    st.markdown(
        f'<div class="translation-note">{escape(translation_note)}</div>',
        unsafe_allow_html=True,
    )

verified_items, unverified_items = collect_verification_items(rates)
with st.expander(ui_text(selected_language, "verification_status_sources")):
    verification_labels = VERIFICATION_DISPLAY_TEXT[selected_language]
    st.markdown(
        verification_summary_text(
            selected_language,
            len(verified_items),
            len(unverified_items),
        )
    )
    st.markdown(f'#### {verification_labels["verified_items"]}')
    st.markdown(
        verification_cards_html(verified_items, selected_language),
        unsafe_allow_html=True,
    )
    st.markdown(f'#### {verification_labels["unverified_items"]}')
    st.markdown(
        verification_cards_html(unverified_items, selected_language),
        unsafe_allow_html=True,
    )

annual_salary = st.number_input(
    annual_salary_input_label(selected_language),
    min_value=MIN_ANNUAL_SALARY,
    max_value=MAX_ANNUAL_SALARY,
    value=DEFAULT_ANNUAL_SALARY,
    step=ANNUAL_SALARY_STEP,
    format="%d",
    key="annual_salary",
)

result = simulate_annual_salary(int(annual_salary), rates)

st.subheader(ui_text(selected_language, "results"))

summary_items = [
    (
        ui_text(selected_language, "annual_take_home"),
        format_display_currency(result.annual_take_home, selected_currency_unit),
    ),
    (
        ui_text(selected_language, "monthly_take_home"),
        format_display_currency(result.monthly_take_home_average, selected_currency_unit),
    ),
    (
        ui_text(selected_language, "employer_burden"),
        format_display_currency(result.insurance.employer_total, selected_currency_unit),
    ),
    (
        ui_text(selected_language, "total_labor_cost"),
        format_display_currency(result.total_labor_cost, selected_currency_unit),
    ),
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

st.table(localized_result_rows(result, selected_currency_unit, selected_language))

st.subheader(ui_text(selected_language, "prefecture_comparison"))
st.markdown(
    f'<p class="app-caption">{escape(comparison_assumption_summary(selected_language, int(annual_salary)))}</p>',
    unsafe_allow_html=True,
)
comparison_results = [
    (
        prefecture_display_name(selected_language, config.code, config.display_name),
        simulate_annual_salary(int(annual_salary), get_rates(config.code)),
    )
    for config in prefecture_configs
]
st.markdown(
    prefecture_comparison_html(comparison_results, language=selected_language),
    unsafe_allow_html=True,
)

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
            "健康保険 標準報酬月額": format_display_currency(
                result.insurance.health_standard_monthly,
                selected_currency_unit,
            ),
            "厚生年金 標準報酬月額": format_display_currency(
                result.insurance.pension_standard_monthly,
                selected_currency_unit,
            ),
            "所得税 課税所得": format_display_currency(
                result.tax.taxable_income_for_income_tax,
                selected_currency_unit,
            ),
            "住民税 課税所得": format_display_currency(
                result.tax.taxable_income_for_resident_tax,
                selected_currency_unit,
            ),
        }
    )

st.subheader(ui_text(selected_language, "salary_examples"))
range_results = simulate_salary_range(rates)
df = results_to_dataframe(range_results)
display_df = localized_results_dataframe(df, selected_currency_unit)

show_details_label, hide_details_label = SALARY_EXAMPLE_DETAIL_LABELS[selected_language]
st.markdown(
    dataframe_to_responsive_html(
        display_df,
        labels=SALARY_EXAMPLE_LABELS[selected_language],
        show_details_label=show_details_label,
        hide_details_label=hide_details_label,
    ),
    unsafe_allow_html=True,
)
