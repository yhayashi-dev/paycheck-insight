import pandas as pd

from src.ui.tables import dataframe_to_responsive_html, format_results_dataframe, format_yen, parse_yen_input


def test_format_yen_uses_commas_and_yen_suffix():
    assert format_yen(5_000_000) == "5,000,000円"


def test_parse_yen_input_accepts_commas_and_yen_suffix():
    assert parse_yen_input("5,000,000円") == 5_000_000


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


def test_dataframe_to_responsive_html_includes_all_required_columns():
    df = pd.DataFrame(
        [
            {
                "年収": "5,000,000円",
                "社会保険料合計": "767,500円",
                "税金合計": "400,000円",
                "年間手取り": "3,832,500円",
                "月平均手取り": "319,375円",
                "健康保険": "250,000円",
                "介護保険": "40,000円",
                "厚生年金": "450,000円",
                "雇用保険": "27,500円",
                "会社負担分": "795,000円",
                "総人件費": "5,795,000円",
            }
        ]
    )

    html = dataframe_to_responsive_html(df)

    assert 'data-label="年間手取り"' in html
    assert 'data-label="月平均手取り"' in html
    assert 'data-label="会社負担分"' in html
    assert 'data-label="総人件費"' in html
    assert "range-mobile-card" in html
    assert "詳細を表示" in html
    assert "<span>社会保険料合計</span>" in html
    assert "<span>健康保険</span>" in html
