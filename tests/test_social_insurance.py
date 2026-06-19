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
