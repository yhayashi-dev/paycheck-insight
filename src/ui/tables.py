from __future__ import annotations

from html import escape

import pandas as pd

from src.models import SimulationResult


def format_yen(value: int) -> str:
    """Format an integer yen amount for Streamlit tables."""

    return f"{value:,.0f}円"


def format_percent(value: float) -> str:
    """Format a percentage value for display."""

    return f"{value:.1f}%"


def parse_yen_input(value: str) -> int:
    """Parse a yen input string such as '5,000,000円' into an integer."""

    normalized = value.replace(",", "").replace("円", "").strip()
    if not normalized:
        return 0
    return int(normalized)


def result_to_display_rows(result: SimulationResult) -> list[dict[str, str]]:
    """Convert a single simulation into labeled display rows."""

    return [
        {"項目": "所得税", "金額": format_yen(result.tax.income_tax)},
        {"項目": "住民税", "金額": format_yen(result.tax.resident_tax)},
        {"項目": "健康保険", "金額": format_yen(result.insurance.health_employee)},
        {"項目": "介護保険", "金額": format_yen(result.insurance.care_employee)},
        {"項目": "厚生年金", "金額": format_yen(result.insurance.pension_employee)},
        {"項目": "雇用保険", "金額": format_yen(result.insurance.employment_employee)},
        {"項目": "社会保険料合計", "金額": format_yen(result.insurance.employee_total)},
        {"項目": "税金合計", "金額": format_yen(result.tax.total)},
        {"項目": "年間手取り", "金額": format_yen(result.annual_take_home)},
        {"項目": "月平均手取り", "金額": format_yen(result.monthly_take_home_average)},
        {"項目": "会社負担分", "金額": format_yen(result.insurance.employer_total)},
        {"項目": "総人件費", "金額": format_yen(result.total_labor_cost)},
    ]


def results_to_dataframe(results: list[SimulationResult]) -> pd.DataFrame:
    """Convert range simulation results into a Streamlit-friendly dataframe."""

    rows = []
    for result in results:
        rows.append(
            {
                "年収": result.annual_salary,
                "月額給与": result.monthly_salary,
                "所得税": result.tax.income_tax,
                "住民税": result.tax.resident_tax,
                "健康保険": result.insurance.health_employee,
                "介護保険": result.insurance.care_employee,
                "厚生年金": result.insurance.pension_employee,
                "雇用保険": result.insurance.employment_employee,
                "社会保険料合計": result.insurance.employee_total,
                "税金合計": result.tax.total,
                "年間手取り": result.annual_take_home,
                "月平均手取り": result.monthly_take_home_average,
                "会社負担分": result.insurance.employer_total,
                "総人件費": result.total_labor_cost,
                "手取り率": result.annual_take_home / result.annual_salary * 100,
            }
        )
    return pd.DataFrame(rows)


def format_results_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Format simulation dataframe values for display without changing calculations."""

    formatted = df.copy()
    yen_columns = [
        "年収",
        "月額給与",
        "所得税",
        "住民税",
        "健康保険",
        "介護保険",
        "厚生年金",
        "雇用保険",
        "社会保険料合計",
        "税金合計",
        "年間手取り",
        "月平均手取り",
        "会社負担分",
        "総人件費",
    ]
    for column in yen_columns:
        formatted[column] = formatted[column].map(format_yen)
    formatted["手取り率"] = formatted["手取り率"].map(format_percent)
    return formatted


IMPORTANT_RANGE_COLUMNS = [
    "年収",
    "月額給与",
    "所得税",
    "住民税",
    "健康保険",
    "年間手取り",
    "月平均手取り",
]

DETAIL_RANGE_COLUMNS = [
    "介護保険",
    "厚生年金",
    "雇用保険",
    "社会保険料合計",
    "税金合計",
    "会社負担分",
    "総人件費",
    "手取り率",
]


def dataframe_to_responsive_html(df: pd.DataFrame) -> str:
    """Render a dataframe as a responsive HTML table for Streamlit markdown."""

    headers = list(df.columns)
    header_html = "".join(f"<th>{escape(column)}</th>" for column in headers)
    body_rows = []
    for _, row in df.iterrows():
        cells = []
        for column in headers:
            value = escape(str(row[column]))
            cells.append(f'<td data-label="{escape(column)}">{value}</td>')
        body_rows.append(f"<tr>{''.join(cells)}</tr>")
    return (
        '<div class="responsive-table-wrap">'
        '<table class="responsive-table">'
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody>"
        "</table>"
        f"{_mobile_range_cards(df)}"
        "</div>"
    )


def _mobile_range_cards(df: pd.DataFrame) -> str:
    cards = []
    for _, row in df.iterrows():
        important_items = "".join(
            _mobile_value_row(column, row[column], "range-mobile-main-row")
            for column in IMPORTANT_RANGE_COLUMNS
            if column in df.columns
        )
        detail_items = "".join(
            _mobile_value_row(column, row[column], "range-mobile-detail-row")
            for column in DETAIL_RANGE_COLUMNS
            if column in df.columns
        )
        cards.append(
            '<section class="range-mobile-card">'
            f"{important_items}"
            '<details class="range-mobile-details">'
            "<summary>詳細を表示</summary>"
            f"{detail_items}"
            "</details>"
            "</section>"
        )
    return '<div class="range-mobile-list">' + "".join(cards) + "</div>"


def _mobile_value_row(column: str, value: object, class_name: str) -> str:
    return (
        f'<div class="{class_name}">'
        f"<span>{escape(column)}</span>"
        f"<strong>{escape(str(value))}</strong>"
        "</div>"
    )
