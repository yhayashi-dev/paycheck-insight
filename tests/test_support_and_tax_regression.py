"""公式保険料額表と国税庁の例から固定した期待値。将来の仕様拡張は含めない。"""
from copy import deepcopy

import pytest
from streamlit.testing.v1 import AppTest

from src.calculators.income_tax import calculate_income_tax
from src.calculators.social_insurance import child_support_monthly, calculate_social_insurance
from src.services.rate_loader import load_rates
from src.services.simulation import simulate_annual_salary
from src.ui.tables import results_to_dataframe, format_results_dataframe


@pytest.mark.parametrize("standard,employee,employer", [
    (58000, 67, 66),    # 表：全額133.4、折半66.7
    (98000, 113, 112),  # 全額225.4、折半112.7
    (110000, 126, 127), # 折半126.5（50銭以下切捨て）
    (150000, 172, 173), # 折半172.5
    (300000, 345, 345),
    (410000, 471, 472), # 折半471.5：Python roundの472を使わない
    (470000, 540, 541),
])
def test_official_support_table_and_payroll_rounding(standard, employee, employer):
    assert child_support_monthly(standard, 0.0023) == (employee, employer)


@pytest.mark.parametrize("region", ["tokyo", "osaka", "kanagawa"])
def test_support_is_national_and_separate_from_employer_only_contribution(region):
    rates = load_rates(prefecture_code=region)
    result = calculate_social_insurance(5_000_000, rates)
    assert result.child_support_employee == 5652  # 471×12
    assert result.child_support_employer == 5664  # 472×12
    assert result.child_care_contribution_employer == 17712  # 410000×0.0036×12
    without = deepcopy(rates)
    without["social_insurance"]["child_support"]["rate"] = 0
    prior = calculate_social_insurance(5_000_000, without)
    assert result.employee_total - prior.employee_total == 5652
    assert result.employer_total - prior.employer_total == 5664
    for field in ("health_employee", "care_employee", "pension_employee", "employment_employee"):
        assert getattr(prior, field) == getattr(result, field)


def test_support_uses_health_standard_above_pension_ceiling():
    result = calculate_social_insurance(10_000_000, load_rates())
    assert result.health_standard_monthly == 830000
    assert result.pension_standard_monthly == 650000
    assert result.child_support_employee == 954 * 12


def test_nta_example_year_end_tax_44600_times_1021_percent():
    # 課税所得892000、所得税44600、復興特別所得税込45536.6 → 45500。
    assert calculate_income_tax(1772000, 0, load_rates()) == (45500, 892000)


@pytest.mark.parametrize("salary_income,social,tax,taxable", [
    (950000, 0, 0, 0),
    (950999, 0, 0, 0),
    (1050000, 0, 5100, 100000),
    (1050000, 1, 5000, 99000),
    (3560000, 757336, 117100, 2122000),
])
def test_tax_rounding_order_and_boundaries(salary_income, social, tax, taxable):
    assert calculate_income_tax(salary_income, social, load_rates()) == (tax, taxable)


def test_support_is_deducted_once_and_flows_to_tax_and_net():
    result = simulate_annual_salary(5000000, load_rates())
    # 3560000 - 680000 - 762988 = 2117012 → 2117000。
    # (211700 - 97500)×1.021 = 116598.2 → 116500。
    assert result.insurance.employee_total == 762988
    assert result.tax.taxable_income_for_income_tax == 2117000
    assert result.tax.income_tax == 116500
    assert result.annual_take_home == 3881312
    df = format_results_dataframe(results_to_dataframe([result]))
    assert df.iloc[0]["子ども・子育て支援金（本人・内数）"] == "5,652円"


def test_effective_date_and_annualization_are_explicit_not_calendar_2026():
    for region in ("tokyo", "osaka", "kanagawa"):
        rates = load_rates(prefecture_code=region)
        config = rates["social_insurance"]["child_support"]
        assert config["effective_from"] == "2026-04-01"
        assert config["payment_from"] == "2026-05"
        assert config["annualization"] == "12_month_equivalent"
        assert "12か月" in rates["metadata"]["notice"]


def test_app_shows_levy_and_annualization_in_both_languages():
    at = AppTest.from_file("app.py").run()
    assert not at.exception
    assert "12か月換算" in at.info[0].value
    assert at.table[0].value.iloc[-2]["金額"] == "5,652円"
    at.selectbox[0].set_value("en").run()
    assert not at.exception
    assert "not the actual amount" in at.info[0].value
    assert at.table[0].value.iloc[-2]["Item"] == "Child support levy (employee, included)"
