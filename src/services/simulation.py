from __future__ import annotations

from typing import Any

from src.calculators.income_tax import calculate_income_tax
from src.calculators.resident_tax import calculate_resident_tax
from src.calculators.salary_income import calculate_salary_income, calculate_salary_income_deduction
from src.calculators.social_insurance import calculate_social_insurance
from src.models import SimulationResult, TaxBreakdown


def simulate_annual_salary(annual_salary: int, rates: dict[str, Any]) -> SimulationResult:
    """Run one take-home pay simulation for the fixed 2026 Tokyo employee scenario."""

    monthly_salary = round(annual_salary / 12)

    # 給与所得控除: 給与収入に応じた控除額。
    salary_income_deduction = calculate_salary_income_deduction(annual_salary, rates)
    # 給与所得: 所得税・住民税の出発点となる給与所得。
    salary_income = calculate_salary_income(annual_salary, rates)
    # 社会保険料: 健康保険、介護保険、厚生年金、雇用保険の本人・会社負担。
    insurance = calculate_social_insurance(annual_salary, rates)
    # 所得税: 給与所得から基礎控除・社会保険料控除を差し引いて算出。
    income_tax, income_taxable = calculate_income_tax(salary_income, insurance.employee_total, rates)
    # 住民税: 入力年収を前年所得相当とみなす概算。
    resident_tax, resident_taxable = calculate_resident_tax(salary_income, insurance.employee_total, rates)

    tax = TaxBreakdown(
        income_tax=income_tax,
        resident_tax=resident_tax,
        taxable_income_for_income_tax=income_taxable,
        taxable_income_for_resident_tax=resident_taxable,
    )

    # 年間手取り: 年収から本人負担の社会保険料と税金を差し引く。
    annual_take_home = annual_salary - insurance.employee_total - tax.total
    # 月平均手取り: 年間手取りを12か月で割った概算。
    monthly_take_home_average = round(annual_take_home / 12)
    # 総人件費: 年収に会社負担分を加えた概算。
    total_labor_cost = annual_salary + insurance.employer_total

    return SimulationResult(
        annual_salary=annual_salary,
        monthly_salary=monthly_salary,
        salary_income_deduction=salary_income_deduction,
        salary_income=salary_income,
        insurance=insurance,
        tax=tax,
        annual_take_home=annual_take_home,
        monthly_take_home_average=monthly_take_home_average,
        total_labor_cost=total_labor_cost,
        provisional=bool(rates["metadata"]["provisional"]),
        notice=rates["metadata"]["notice"],
    )


def simulate_salary_range(rates: dict[str, Any], start: int = 2_000_000, stop: int = 10_000_000, step: int = 1_000_000) -> list[SimulationResult]:
    """Run simulations for the annual salary table."""

    return [simulate_annual_salary(salary, rates) for salary in range(start, stop + 1, step)]
