from __future__ import annotations

from typing import Any

from src.calculators.common import round_down_to_unit, yen


def calculate_income_tax(salary_income: int, social_insurance_employee: int, rates: dict[str, Any]) -> tuple[int, int]:
    """Calculate annual national income tax including reconstruction surtax."""

    income_tax = rates["income_tax"]
    rounding = rates["rounding"]

    # 所得税の課税所得: 給与所得から基礎控除と社会保険料控除を差し引き、1,000円未満を切り捨てる。
    basic_deduction = _find_basic_deduction(salary_income, _get_basic_deduction_brackets(income_tax))
    taxable_income = salary_income - basic_deduction - social_insurance_employee
    taxable_income = round_down_to_unit(max(taxable_income, 0), rounding["taxable_income_unit"])

    bracket = _find_tax_bracket(taxable_income, income_tax["brackets"])
    # 所得税本税: 課税所得 x 税率 - 速算控除で計算する。
    base_tax = max(taxable_income * bracket["rate"] - bracket["deduction"], 0)
    # 復興特別所得税: 所得税本税に復興特別所得税率を掛けて合算する。
    total_tax = base_tax * (1 + income_tax["reconstruction_surtax_rate"])
    return yen(total_tax), taxable_income


def _get_basic_deduction_brackets(income_tax: dict[str, Any]) -> list[dict[str, int | None]]:
    brackets = income_tax.get("basic_deduction_brackets")
    if brackets is None:
        raise ValueError(
            "income_tax.basic_deduction_brackets is required. "
            "The 2026 income-tax basic deduction must be configured as income-based brackets."
        )
    if not isinstance(brackets, list):
        raise ValueError("income_tax.basic_deduction_brackets must be a list.")
    return brackets


def _find_basic_deduction(total_income: int, brackets: list[dict[str, int | None]]) -> int:
    for bracket in brackets:
        upper = bracket["upper"]
        if upper is None or total_income <= upper:
            return int(bracket["deduction"])
    raise ValueError("Income tax basic deduction bracket was not found.")


def _find_tax_bracket(taxable_income: int, brackets: list[dict[str, int | float | None]]) -> dict[str, int | float | None]:
    for bracket in brackets:
        upper = bracket["upper"]
        if taxable_income >= bracket["lower"] and (upper is None or taxable_income < upper):
            return bracket
    raise ValueError("Income tax bracket was not found.")
