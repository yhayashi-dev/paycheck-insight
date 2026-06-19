from src.calculators.salary_income import calculate_salary_income, calculate_salary_income_deduction
from src.services.rate_loader import load_rates


def test_salary_income_deduction_uses_configured_bracket():
    rates = load_rates()

    assert calculate_salary_income_deduction(1_500_000, rates) == 650_000
    assert calculate_salary_income(1_500_000, rates) == 850_000
    assert calculate_salary_income_deduction(5_000_000, rates) == 1_440_000
    assert calculate_salary_income(5_000_000, rates) == 3_560_000
