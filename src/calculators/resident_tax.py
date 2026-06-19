from __future__ import annotations

from typing import Any

from src.calculators.common import round_down_to_unit, yen


def calculate_resident_tax(salary_income: int, social_insurance_employee: int, rates: dict[str, Any]) -> tuple[int, int]:
    """Calculate annual resident tax using configured provisional Tokyo values."""

    resident_tax = rates["resident_tax"]
    rounding = rates["rounding"]
    municipality_class = resident_tax["municipality_class"]

    if _is_non_taxable_single_no_dependents(salary_income, resident_tax, municipality_class):
        return 0, 0

    # 住民税の課税所得: 給与所得から住民税の基礎控除と社会保険料控除を差し引き、1,000円未満を切り捨てる。
    taxable_income = salary_income - resident_tax["basic_deduction"] - social_insurance_employee
    taxable_income = round_down_to_unit(max(taxable_income, 0), rounding["taxable_income_unit"])

    # 所得割: 課税所得に住民税所得割率を掛け、人的控除差に基づく調整控除を差し引く。
    income_portion = taxable_income * resident_tax["income_rate"]
    adjustment_deduction = _calculate_adjustment_deduction(salary_income, taxable_income, rates)
    income_portion = max(income_portion - adjustment_deduction, 0)
    # 均等割・森林環境税: 設定ファイルの年額を所得割に加算する。
    total_tax = income_portion + resident_tax["per_capita"] + resident_tax["forest_environment_tax"]
    total_tax = round_down_to_unit(total_tax, resident_tax["tax_amount_unit"])
    return yen(total_tax), taxable_income


def _is_non_taxable_single_no_dependents(total_income: int, resident_tax: dict[str, Any], municipality_class: str) -> bool:
    """Apply the configured no-dependent non-taxable threshold for the municipality class."""

    non_taxable = resident_tax["non_taxable"][municipality_class]
    return total_income <= non_taxable["no_dependents_total_income"]


def _calculate_adjustment_deduction(total_income: int, taxable_income: int, rates: dict[str, Any]) -> int:
    resident_tax = rates["resident_tax"]
    adjustment = resident_tax["adjustment_deduction"]
    if not adjustment["enabled"] or taxable_income <= 0:
        return 0

    personal_deduction_difference = _find_income_tax_basic_deduction(total_income, rates) - resident_tax["basic_deduction"]
    personal_deduction_difference = max(personal_deduction_difference, 0)
    if personal_deduction_difference == 0:
        return 0

    if taxable_income <= adjustment["threshold"]:
        deduction_base = min(personal_deduction_difference, taxable_income)
        deduction = deduction_base * adjustment["rate"]
    else:
        deduction_base = personal_deduction_difference - (taxable_income - adjustment["threshold"])
        deduction = max(deduction_base * adjustment["rate"], adjustment["minimum"])

    return yen(deduction)


def _find_income_tax_basic_deduction(total_income: int, rates: dict[str, Any]) -> int:
    for bracket in rates["income_tax"]["basic_deduction_brackets"]:
        upper = bracket["upper"]
        if upper is None or total_income <= upper:
            return int(bracket["deduction"])
    raise ValueError("Income tax basic deduction bracket was not found.")
