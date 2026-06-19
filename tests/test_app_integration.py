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


def test_verification_html_includes_mobile_card_fields_and_desktop_table():
    import app

    html = app.verification_table_html(
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

    assert 'class="verification-table"' in html
    assert 'class="verification-mobile-list"' in html
    assert 'class="verification-mobile-card"' in html
    assert "社会保険料" in html
    assert "健康保険料率" in html
    assert "確認済み" in html
    assert "適用年度・条件" in html
    assert "適用開始日" in html
    assert "出典" in html
