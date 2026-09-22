from __future__ import annotations

from typing import Any


def calculate_salary_income(annual_salary: int, rates: dict[str, Any], *, income_year: int | None = None) -> int:
    """Official annual salary-income tables; national 2026 and local FY2026 differ."""
    year = income_year or rates['salary_income_deduction']['table_year']
    if year not in (2025, 2026):
        raise ValueError('Unsupported salary income year')
    if annual_salary < 0:
        raise ValueError('Salary must be nonnegative')
    if year == 2026:
        if annual_salary < 741000:
            return 0
        if annual_salary < 2191000:
            return annual_salary - 740000
        if annual_salary < 2193000:
            return 1451000
        if annual_salary < 2196000:
            return 1453000
        if annual_salary < 2200000:
            return 1456000
    else:
        if annual_salary < 651000:
            return 0
        if annual_salary < 1900000:
            return annual_salary - 650000
    # NTA: A / 4, truncate below 1,000 yen, then multiply.
    quarter = annual_salary // 4000 * 1000
    if annual_salary < 3600000:
        return quarter * 28 // 10 - 80000
    if annual_salary < 6600000:
        return quarter * 32 // 10 - 440000
    if annual_salary < 8500000:
        return annual_salary * 9 // 10 - 1100000
    return annual_salary - 1950000


def calculate_salary_income_deduction(annual_salary: int, rates: dict[str, Any]) -> int:
    """Effective deduction, capped at gross salary for the zero-income bands."""
    return annual_salary - calculate_salary_income(annual_salary, rates)
