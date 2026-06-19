from __future__ import annotations

from typing import Any

from src.calculators.common import yen


def calculate_salary_income_deduction(annual_salary: int, rates: dict[str, Any]) -> int:
    """Calculate給与所得控除 from the configured bracket table."""

    brackets = rates["salary_income_deduction"]["brackets"]
    for bracket in brackets:
        upper = bracket["upper"]
        if upper is None or annual_salary <= upper:
            # 給与所得控除: 固定額がある区分は固定額、その他は収入 x 率 + 調整額で計算する。
            if bracket["fixed"]:
                return yen(bracket["fixed"])
            return yen(annual_salary * bracket["rate"] + bracket["adjustment"])
    raise ValueError("Salary income deduction bracket was not found.")


def calculate_salary_income(annual_salary: int, rates: dict[str, Any]) -> int:
    """Calculate給与所得 after salary income deduction."""

    deduction = calculate_salary_income_deduction(annual_salary, rates)
    # 給与所得: 給与収入から給与所得控除を差し引き、0円未満にはしない。
    return max(annual_salary - deduction, 0)
