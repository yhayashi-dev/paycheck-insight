from __future__ import annotations

from typing import Any

from src.calculators.common import yen
from src.models import InsuranceBreakdown


def find_standard_monthly(monthly_salary: int, table: list[dict[str, int | None]]) -> int:
    """Find the standard monthly remuneration amount for a monthly salary."""

    for row in table:
        lower = row["lower"]
        upper = row["upper"]
        if monthly_salary >= lower and (upper is None or monthly_salary < upper):
            return int(row["standard"])
    raise ValueError("Standard monthly remuneration bracket was not found.")


def calculate_social_insurance(annual_salary: int, rates: dict[str, Any]) -> InsuranceBreakdown:
    """Calculate annual employee and employer social-insurance amounts."""

    monthly_salary = annual_salary / 12
    social = rates["social_insurance"]
    tables = social["standard_monthly_remuneration"]

    # 健康保険: 年収を12か月均等支給した月額給与から標準報酬月額を選び、労使折半で計算する。
    health_standard = find_standard_monthly(int(monthly_salary), tables["health"])
    monthly_health_total = health_standard * social["health_insurance_rate"]
    monthly_health_employee = yen(monthly_health_total / 2)
    monthly_health_employer = yen(monthly_health_total / 2)

    # 介護保険: 52歳は40歳以上65歳未満のため、標準報酬月額に介護保険料率を掛けて労使折半する。
    monthly_care_total = health_standard * social["care_insurance_rate"]
    monthly_care_employee = yen(monthly_care_total / 2)
    monthly_care_employer = yen(monthly_care_total / 2)

    # 厚生年金: 厚生年金用の標準報酬月額を選び、厚生年金保険料率を労使折半する。
    pension_standard = find_standard_monthly(int(monthly_salary), tables["pension"])
    monthly_pension_total = pension_standard * social["pension_rate"]
    monthly_pension_employee = yen(monthly_pension_total / 2)
    monthly_pension_employer = yen(monthly_pension_total / 2)

    employment = social["employment_insurance"]
    # 雇用保険: 給与収入を賃金額として、労働者負担率を掛ける。
    employment_employee = yen(annual_salary * employment["worker_rate"])
    # 雇用保険の会社負担: 給与収入に事業主負担率を掛ける。
    employment_employer = yen(annual_salary * employment["employer_rate"])

    # 子ども・子育て拠出金: 会社のみ負担する項目として総人件費に含める。
    child_care_contribution = yen(pension_standard * social["child_care_contribution_rate"] * 12)

    return InsuranceBreakdown(
        health_employee=monthly_health_employee * 12,
        health_employer=monthly_health_employer * 12,
        care_employee=monthly_care_employee * 12,
        care_employer=monthly_care_employer * 12,
        pension_employee=monthly_pension_employee * 12,
        pension_employer=monthly_pension_employer * 12,
        employment_employee=employment_employee,
        employment_employer=employment_employer,
        child_care_contribution_employer=child_care_contribution,
        health_standard_monthly=health_standard,
        pension_standard_monthly=pension_standard,
    )
