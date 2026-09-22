from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
from typing import Any
from src.calculators.common import round_down_to_unit


def calculate_resident_tax(salary_income: int, social_insurance_employee: int, rates: dict[str, Any]) -> tuple[int, int]:
    """FY2026 local tax: single/no dependents, no other deductions or credits."""
    local = rates['resident_tax']
    # Salary-only scope: the two statutory income bases coincide. Neither is
    # taxable income after deductions. Never infer one levy's exemption from another.
    keys = ('income_levy_exemption', 'per_capita_levy_exemption',
            'forest_environment_tax_exemption')
    if any(key not in local for key in keys):
        raise ValueError('exemption_evidence_missing: migrate legacy settings explicitly')
    income_exempt, per_capita_exempt, forest_exempt = (
        salary_income <= local[key]['inclusive_limit'] for key in keys)
    taxable = round_down_to_unit(max(salary_income - local['basic_deduction'] - social_insurance_employee, 0), 1000)
    base = _adjustment_base(salary_income, taxable, local)
    amounts = []
    for part in ([] if income_exempt else local['income_components']):
        assessed = int(Decimal(taxable) * Decimal(str(part['income_rate'])))
        credit = Decimal(base) * Decimal(str(part['adjustment_rate']))
        amounts.append(Fraction(max(Decimal(assessed) - credit, 0)))
    # Local Tax Act Supplementary Provisions 3-3(2),(5): marginal relief,
    # apportioned by assessed component amounts BEFORE final 100-yen rounding.
    # This is distinct from the personal-allowance adjustment credit above.
    total = sum(amounts)
    available = max(salary_income - local['income_levy_exemption']['inclusive_limit'], 0)
    if total > available:
        amounts = [amount * available / total for amount in amounts]
    income_portion = sum(int(amount // 100) * 100 for amount in amounts)
    fixed = (0 if per_capita_exempt else local['per_capita'])
    forest = (0 if forest_exempt else local['forest_environment_tax'])
    return income_portion + fixed + forest, 0 if income_exempt else taxable


def _adjustment_base(total_income: int, taxable: int, local: dict[str, Any]) -> int:
    adjustment = local['adjustment_deduction']
    if not adjustment['enabled'] or total_income > adjustment['total_income_limit']:
        return 0
    # Statutory old-system personal allowance difference; NOT current national minus local.
    difference = adjustment['personal_difference']
    if taxable <= adjustment['threshold']:
        return min(difference, taxable)
    return max(difference - (taxable - adjustment['threshold']), 50000)
