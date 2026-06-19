from src.calculators.social_insurance import calculate_social_insurance, find_standard_monthly
from src.services.rate_loader import load_rates


def test_standard_monthly_remuneration_selects_expected_health_grade():
    rates = load_rates()
    table = rates["social_insurance"]["standard_monthly_remuneration"]["health"]

    assert find_standard_monthly(416_666, table) == 410_000


def test_social_insurance_splits_employee_and_employer_amounts():
    rates = load_rates()
    result = calculate_social_insurance(5_000_000, rates)

    assert result.health_employee > 0
    assert result.care_employee > 0
    assert result.pension_employee > 0
    assert result.health_employee == 242_304
    assert result.care_employee == 39_852
    assert result.employment_employee == 25_000
    assert result.employment_employer == 42_500
    assert result.employer_total > result.employee_total


def test_social_insurance_rates_are_officially_confirmed_without_value_changes():
    rates = load_rates()
    social = rates["social_insurance"]

    assert social["health_insurance_rate"] == 0.0985
    assert social["care_insurance_rate"] == 0.0162
    assert social["pension_rate"] == 0.183
    assert social["employment_insurance"] == {
        "worker_rate": 0.0050,
        "employer_rate": 0.0085,
    }
    assert social["child_care_contribution_rate"] == 0.0036

    confirmed_items = {
        item["item"] for item in social["verification"] if not item["provisional"]
    }
    assert confirmed_items == {
        "健康保険料率",
        "介護保険料率",
        "厚生年金保険料率",
        "標準報酬月額",
        "雇用保険料率",
        "子ども・子育て拠出金率",
    }
