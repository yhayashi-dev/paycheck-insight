"""Resolve independently selected tax years, municipality and insurer/month.

The compatibility result is a fresh dictionary, never inherited from Tokyo.
Effective dates describe the source; coverage_months limits what this app accepts.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from copy import deepcopy
from src.services.settings_validation import read_json, require_valid
from pathlib import Path
from datetime import date
from typing import Any

SETTINGS_FILE = Path(__file__).resolve().parents[2] / 'data' / 'period_settings.json'

@dataclass(frozen=True)
class CalculationContext:
    income_year: int
    municipality_id: str
    fiscal_year: int
    insurer_id: str
    branch_id: str
    effective_month: str
    business_type: str = 'general'
    mode: str = 'annualized_12_month'

@dataclass(frozen=True)
class PreviousYearInputs:
    """Explicit local-tax input. No monthly/calendar inference."""
    income_year: int
    annual_salary: int
    social_insurance_paid: int


def load_calculation_rates(context: CalculationContext, *, settings_file: Path = SETTINGS_FILE,
                           assumptions: dict[str, Any] | None = None) -> dict[str, Any]:
    if context.mode != 'annualized_12_month':
        raise ValueError('unsupported_calculation_mode: calendar-year mode is not implemented')
    try:
        selected_month = date.fromisoformat(context.effective_month + '-01')
    except (ValueError, TypeError) as exc:
        raise ValueError('invalid_effective_month') from exc
    registry = read_json(settings_file)
    require_valid(registry)
    def select(section: str, *keys: object) -> dict[str, Any]:
        try:
            record = registry[section]
            for key in keys:
                record = record[str(key)]
        except KeyError as exc:
            raise ValueError(f'unsupported_setting: {section}/{keys}') from exc
        if 'coverage_months' in record and context.effective_month not in record['coverage_months']:
            raise ValueError(f'unsupported_month: {section}')
        if 'coverage_months' in record:
            if record['effective_month'] != context.effective_month:
                raise ValueError(f'setting_month_mismatch: {section}')
            provenance = record['provenance']
            start = date.fromisoformat(provenance['effective_from'])
            end = provenance.get('effective_to')
            if selected_month < start or (end is not None and selected_month > date.fromisoformat(end)):
                raise ValueError(f'setting_outside_effective_period: {section}')
        return deepcopy(record)
    national = select('national_tax', context.income_year)
    local = select('resident_tax', context.municipality_id, context.fiscal_year)
    health = select('health_insurance', context.insurer_id, context.branch_id, context.effective_month)
    pension = select('pension', context.effective_month)
    employment = select('employment_insurance', context.business_type, context.effective_month)
    support = select('child_support', context.effective_month)
    if national['values']['salary_income_deduction']['table_year'] != context.income_year:
        raise ValueError('national_salary_year_mismatch')
    if national['income_year'] != context.income_year or local['fiscal_year'] != context.fiscal_year:
        raise ValueError('setting_year_mismatch')
    if local['municipality_id'] != context.municipality_id or local['previous_income_year'] != context.fiscal_year - 1:
        raise ValueError('resident_period_mismatch')
    if local['values']['salary_income_year'] != local['previous_income_year']:
        raise ValueError('salary_income_year_mismatch')
    result = deepcopy(registry['common'])
    result.update(national['values'])
    result['resident_tax'] = local['values']
    social = health['values']
    social['standard_monthly_remuneration'] = result.pop('standard_monthly_remuneration')
    social.update(pension['values'])
    social['employment_insurance'] = employment['values']
    social['child_support'] = support['values']
    result['social_insurance'] = social
    result['calculation_context'] = asdict(context)
    result['assumptions'] = deepcopy(result['assumptions'] if assumptions is None else assumptions)
    if result['assumptions'].get('previous_year_policy') not in ('same_as_current', 'explicit'):
        raise ValueError('unsupported_previous_year_policy')
    result['provenance'] = {k: v['provenance'] for k, v in [('national_tax',national),('resident_tax',local),('health_insurance',health),('pension',pension),('employment_insurance',employment),('child_support',support)]}
    return result
