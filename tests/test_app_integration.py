import os
from pathlib import Path
import subprocess
import sys

from src.services.simulation import simulate_annual_salary


def test_app_imports_local_src_package_outside_project_directory(tmp_path):
    project_root = Path(__file__).resolve().parents[1]
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)

    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import runpy; "
                f"runpy.run_path({str(project_root / 'app.py')!r}, run_name='__main__')"
            ),
        ],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr


def test_app_get_rates_loads_default_rates_for_500_man_yen_case():
    import app

    rates = app.get_rates("tokyo")
    result = simulate_annual_salary(5_000_000, rates)

    assert rates["income_tax"]["basic_deduction_brackets"][2]["deduction"] == 680_000
    assert result.salary_income == 3_560_000
    assert result.tax.taxable_income_for_income_tax == 2_122_000
    assert result.tax.income_tax == 117_109
    assert result.tax.taxable_income_for_resident_tax == 2_372_000
    assert result.tax.resident_tax == 239_700
    assert result.insurance.employee_total == 757_336
    assert result.insurance.employer_total == 792_548
    assert result.annual_take_home == 3_885_855
    assert result.monthly_take_home_average == 323_821
    assert result.total_labor_cost == 5_792_548

    japanese_rows = app.localized_result_rows(result, "円", "ja")
    assert japanese_rows[0] == {"項目": "所得税", "金額": "117,109円"}

    english_rows = app.localized_result_rows(result, "JPY", "en")
    assert english_rows[0] == {"Item": "Income tax", "Amount": "117,109 JPY"}
    assert english_rows[3]["Item"] == "Long-term care insurance"
    assert english_rows[4]["Item"] == "Employees’ pension"
    assert english_rows[6]["Item"] == "Total social insurance"
    assert english_rows[7]["Item"] == "Total taxes"
    assert english_rows[8] == {
        "Item": "Annual take-home pay",
        "Amount": "3,885,855 JPY",
    }


def test_app_ui_text_defaults_to_japanese_and_supports_major_english_labels():
    import app

    assert app.ui_text("ja", "title") == "2026年 手取り試算"
    assert app.ui_text("unknown", "prefecture") == "都道府県"
    assert app.ui_text("en", "title") == "2026 Take-home Pay Simulator"
    assert app.ui_text("en", "subtitle") == (
        "Estimate taxes, social insurance, and take-home pay for employees in Japan"
    )
    assert app.ui_text("en", "annual_salary") == "Annual salary"
    assert app.ui_text("en", "verification_status_sources") == (
        "Verification status and sources"
    )
    assert app.currency_unit("ja") == "円"
    assert app.currency_unit("en") == "JPY"
    assert app.format_display_currency(5_000_000, "円") == "5,000,000円"
    assert app.format_display_currency(5_000_000, "JPY") == "5,000,000 JPY"
    assert app.parse_currency_input("5,000,000 JPY") == 5_000_000
    assert app.SALARY_EXAMPLE_LABELS["ja"]["年収"] == "年収"
    assert app.SALARY_EXAMPLE_LABELS["en"]["年収"] == "Annual salary"
    assert app.SALARY_EXAMPLE_LABELS["en"]["厚生年金"] == "Employees' pension"
    assert app.SALARY_EXAMPLE_DETAIL_LABELS["en"] == ("Show details", "Hide details")


def test_warning_message_preserves_japanese_metadata_and_translates_english_mode():
    import app

    metadata = app.get_rates("osaka")["metadata"]

    assert app.warning_message("ja", metadata) == metadata["notice"]
    assert app.warning_message("unknown", metadata) == metadata["notice"]
    assert app.warning_message("en", metadata) == app.ENGLISH_WARNING_MESSAGE
    assert app.warning_message("en", metadata).startswith("Some items are still unverified.")
    assert "local tax rounding rules" in app.warning_message("en", metadata)


def test_partial_translation_note_is_only_shown_for_english_mode():
    import app

    assert app.partial_translation_note("ja") is None
    assert app.partial_translation_note("unknown") is None
    assert app.partial_translation_note("en") == app.ENGLISH_PARTIAL_TRANSLATION_NOTE
    assert "official terms and source titles" in app.partial_translation_note("en")
    assert "partially translated" in app.partial_translation_note("en")


def test_assumption_summary_preserves_japanese_and_translates_prefecture_names():
    import app

    tokyo_metadata = app.get_rates("tokyo")["metadata"]
    assert app.assumption_summary("ja", "tokyo", tokyo_metadata) == (
        "東京都・52歳・単身・扶養なし・会社員・協会けんぽ・給与収入のみ・"
        "賞与なし・12か月均等支給の概算です。"
    )

    expected_prefecture_names = {
        "tokyo": "Tokyo",
        "osaka": "Osaka",
        "kanagawa": "Kanagawa (Yokohama assumed)",
    }
    for prefecture_code, english_name in expected_prefecture_names.items():
        metadata = app.get_rates(prefecture_code)["metadata"]
        summary = app.assumption_summary("en", prefecture_code, metadata)
        assert summary.startswith(f"{english_name} · Age 52 · Single · No dependents")
        assert summary.endswith("No bonus · Paid evenly over 12 months.")


def test_prefecture_display_names_change_language_without_changing_rate_keys():
    import app

    expected_names = {
        "tokyo": ("東京都", "Tokyo"),
        "osaka": ("大阪府", "Osaka"),
        "kanagawa": ("神奈川県（横浜市想定）", "Kanagawa (Yokohama assumed)"),
    }

    for prefecture_code, (japanese_name, english_name) in expected_names.items():
        assert app.prefecture_display_name("ja", prefecture_code, japanese_name) == japanese_name
        assert app.prefecture_display_name("en", prefecture_code, japanese_name) == english_name
        assert app.get_rates(prefecture_code)["regional_scope"]["prefecture_code"] == prefecture_code


def test_prefecture_comparison_uses_english_labels_when_requested():
    import app

    tokyo_result = simulate_annual_salary(5_000_000, app.get_rates("tokyo"))
    osaka_result = simulate_annual_salary(5_000_000, app.get_rates("osaka"))

    html = app.prefecture_comparison_html(
        tokyo_result,
        osaka_result,
        language="en",
    )

    assert "Annual take-home pay" in html
    assert "Monthly average take-home pay" in html
    assert "Employer burden" in html
    assert "Total labor cost" in html
    assert "Tokyo" in html
    assert "Osaka" in html
    assert "Difference (Osaka - Tokyo)" in html
    assert (
        "Osaka compared with Tokyo: "
        '<span class="comparison-difference-value">-5,773 JPY</span>' in html
    )
    assert "3,885,855 JPY" in html


def test_prefecture_comparison_assumption_summary_changes_language():
    import app

    assert app.comparison_assumption_summary("ja") == (
        "年収 5,000,000円・52歳・単身・扶養なし・賞与なし・"
        "12か月均等支給で比較しています。"
    )
    assert app.comparison_assumption_summary("en") == (
        "Annual salary 5,000,000 JPY · Age 52 · Single · No dependents · "
        "No bonus · Paid evenly over 12 months."
    )


def test_app_verification_metadata_splits_confirmed_and_unconfirmed_items():
    import app

    rates = app.get_rates("tokyo")
    verified_items, unverified_items = app.collect_verification_items(rates)

    assert rates["metadata"]["provisional"] is True
    assert rates["salary_income_deduction"]["provisional"] is False
    assert rates["income_tax"]["provisional"] is True
    assert rates["resident_tax"]["provisional"] is False
    assert rates["social_insurance"]["provisional"] is True
    assert "一部未確認項目あり" in rates["metadata"]["notice"]

    assert any(item["item"] == "所得税の基礎控除" for item in verified_items)
    assert any(item["item"] == "均等割" for item in verified_items)
    assert len(verified_items) == 21
    assert len(unverified_items) == 2
    assert all(
        item["status"] == "確認済み"
        for item in verified_items
        if item["section"] == "社会保険料"
    )
    assert {
        item["item"]
        for item in verified_items
        if item["section"] == "社会保険料"
    } == {
        "健康保険料率",
        "介護保険料率",
        "厚生年金保険料率",
        "標準報酬月額",
        "雇用保険料率",
        "子ども・子育て拠出金率",
    }
    assert any(item["item"] == "所得税額の最終端数処理" for item in unverified_items)
    assert any(
        item["item"] == "子ども・子育て支援金率（計算未反映）"
        and item["status"] == "計算未反映"
        for item in unverified_items
    )
    assert all("source_name" in item for item in verified_items + unverified_items)
    assert all("applicable_period" in item for item in verified_items + unverified_items)
    assert all(
        item["effective_from"] != "-" and item["last_verified_on"] == "2026-06-20"
        for item in verified_items + unverified_items
        if item["section"] == "社会保険料"
    )


def test_app_osaka_rates_use_osaka_sources_and_preserve_common_sources():
    import app

    rates = app.get_rates("osaka")
    verified_items, unverified_items = app.collect_verification_items(rates)

    assert rates["metadata"]["prefecture"] == "大阪府"
    assert any(
        item["item"] == "健康保険料率"
        and "大阪府保険料額表" in item["source_name"]
        for item in verified_items
    )
    assert any(
        item["item"] == "非課税判定（大阪市）"
        and item["source_url"].startswith("https://www.city.osaka.lg.jp/")
        for item in verified_items
    )
    assert any(
        item["item"] == "市民税・府民税の個別100円未満切捨て（計算未反映）"
        for item in unverified_items
    )
    assert not any(
        item["section"] in {"住民税", "社会保険料"}
        and "東京都" in item["source_name"]
        for item in verified_items + unverified_items
    )


def test_verification_html_uses_responsive_cards_with_required_fields():
    import app

    html = app.verification_cards_html(
        [
            {
                "section": "社会保険料",
                "item": "健康保険料率",
                "status": "確認済み",
                "applicable_period": "2026年度・大阪府",
                "effective_from": "2026年3月分",
                "last_verified_on": "2026-06-20",
                "source_name": "協会けんぽ 大阪府保険料額表",
                "source_url": "https://example.com/osaka.pdf",
            }
        ]
    )

    assert 'class="verification-card-list"' in html
    assert 'class="verification-card"' in html
    assert "<table" not in html
    assert "社会保険料" in html
    assert "健康保険料率" in html
    assert "分類" in html
    assert "項目" in html
    assert "状態" in html
    assert "確認済み" in html
    assert "適用年度・条件" in html
    assert "適用開始日" in html
    assert "出典" in html
    assert 'href="https://example.com/osaka.pdf"' in html
    assert 'target="_blank"' in html

    english_html = app.verification_cards_html(
        [
            {
                "section": "社会保険料",
                "item": "健康保険料率",
                "status": "確認済み",
                "applicable_period": "2026年度・大阪府",
                "effective_from": "2026年3月分",
                "last_verified_on": "2026-06-20",
                "source_name": "協会けんぽ 大阪府保険料額表",
                "source_url": "https://example.com/osaka.pdf",
            }
        ],
        language="en",
    )
    assert "Category" in english_html
    assert "Item" in english_html
    assert "Status" in english_html
    assert "Verified" in english_html
    assert "Applicable year / conditions" in english_html
    assert "Effective date" in english_html
    assert "Last verified date" in english_html
    assert "Source" in english_html
    assert "協会けんぽ 大阪府保険料額表" in english_html


def test_verification_summary_changes_language_without_changing_counts():
    import app

    assert app.verification_summary_text("ja", 21, 2) == (
        "一部未確認項目あり。確認済み 21 件、未確認 2 件です。"
    )
    assert app.verification_summary_text("en", 21, 2) == (
        "Some items are still unverified. Verified: 21, Unverified: 2."
    )


def test_prefecture_comparison_html_uses_existing_500_man_yen_results():
    import app

    tokyo_result = simulate_annual_salary(5_000_000, app.get_rates("tokyo"))
    osaka_result = simulate_annual_salary(5_000_000, app.get_rates("osaka"))

    html = app.prefecture_comparison_html(tokyo_result, osaka_result)

    assert 'class="comparison-prefecture-grid"' in html
    assert "東京都" in html
    assert "大阪府" in html
    assert "3,885,855円" in html
    assert "3,880,082円" in html
    assert "757,336円" in html
    assert "764,224円" in html
    assert "356,809円" in html
    assert "355,694円" in html
    assert "792,548円" in html
    assert "799,436円" in html
    assert "5,792,548円" in html
    assert "5,799,436円" in html
    assert (
        "大阪府は東京都より "
        '<span class="comparison-difference-value">-5,773円</span>' in html
    )
    assert (
        "大阪府は東京都より "
        '<span class="comparison-difference-value">-481円</span>' in html
    )
    assert (
        "大阪府は東京都より "
        '<span class="comparison-difference-value">+6,888円</span>' in html
    )
    assert "<table" not in html
