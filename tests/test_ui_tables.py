import pandas as pd

from src.ui.tables import (
    dataframe_to_responsive_html,
    format_currency,
    format_results_dataframe,
    format_yen,
    parse_yen_input,
)


def test_format_yen_uses_commas_and_yen_suffix():
    assert format_yen(5_000_000) == "5,000,000円"
    assert format_currency(5_000_000, "JPY") == "5,000,000 JPY"


def test_parse_yen_input_accepts_commas_and_yen_suffix():
    assert parse_yen_input("5,000,000円") == 5_000_000
    assert parse_yen_input("5,000,000 JPY") == 5_000_000


def test_format_results_dataframe_formats_money_columns():
    df = pd.DataFrame(
        [
            {
                "年収": 5_000_000,
                "月額給与": 416_667,
                "所得税": 150_000,
                "住民税": 250_000,
                "健康保険": 250_000,
                "介護保険": 40_000,
                "厚生年金": 450_000,
                "雇用保険": 27_500,
                "社会保険料合計": 767_500,
                "税金合計": 400_000,
                "年間手取り": 3_832_500,
                "月平均手取り": 319_375,
                "会社負担分": 795_000,
                "総人件費": 5_795_000,
                "手取り率": 76.65,
            }
        ]
    )

    formatted = format_results_dataframe(df)

    assert formatted.loc[0, "年収"] == "5,000,000円"
    assert formatted.loc[0, "年間手取り"] == "3,832,500円"
    assert formatted.loc[0, "総人件費"] == "5,795,000円"
    assert formatted.loc[0, "手取り率"] == "76.7%"

    english_formatted = format_results_dataframe(df, "JPY")
    assert english_formatted.loc[0, "年収"] == "5,000,000 JPY"
    assert english_formatted.loc[0, "年間手取り"] == "3,832,500 JPY"


def test_dataframe_to_responsive_html_uses_cards_without_a_table():
    df = pd.DataFrame(
        [
            {
                "年収": "5,000,000円",
                "月額給与": "416,667円",
                "所得税": "117,109円",
                "住民税": "239,700円",
                "健康保険": "242,304円",
                "介護保険": "39,852円",
                "厚生年金": "450,180円",
                "雇用保険": "25,000円",
                "社会保険料合計": "757,336円",
                "税金合計": "356,809円",
                "年間手取り": "3,885,855円",
                "月平均手取り": "323,821円",
                "会社負担分": "792,548円",
                "総人件費": "5,792,548円",
                "手取り率": "77.7%",
            }
        ]
    )

    html = dataframe_to_responsive_html(df)

    assert "<table" not in html
    assert html.count('class="range-mobile-card"') == 1
    assert "詳細を表示" in html
    assert "詳細を閉じる" in html
    for label in [
        "年収",
        "月額給与",
        "所得税",
        "住民税",
        "社会保険料合計",
        "税金合計",
        "年間手取り",
        "月平均手取り",
    ]:
        assert f"<span>{label}</span>" in html

    english_html = dataframe_to_responsive_html(
        df,
        labels={
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
        show_details_label="Show details",
        hide_details_label="Hide details",
    )

    assert "Annual salary" in english_html
    assert "Monthly average take-home pay" in english_html
    assert "Long-term care insurance" in english_html
    assert "Employees&#x27; pension" in english_html
    assert "Show details" in english_html
    assert "Hide details" in english_html
    assert "5,000,000円" in english_html
