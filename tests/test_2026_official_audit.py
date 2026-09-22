"""Independent official-table/boundary expectations. Sources: docs/audits/2026-09-17."""
from copy import deepcopy
import pytest
from src.calculators.salary_income import calculate_salary_income
from src.calculators.income_tax import calculate_income_tax, _find_basic_deduction
from src.calculators.resident_tax import calculate_resident_tax
from src.calculators.social_insurance import calculate_social_insurance
from src.services.rate_loader import load_rates


@pytest.mark.parametrize('salary,income', [
    (740999,0),(741000,1000),(1500000,760000),(2190999,1450999),
    (2191000,1451000),(2192999,1451000),(2193000,1453000),
    (2195999,1453000),(2196000,1456000),(2199999,1456000),
    (2200000,1460000),(3599999,2437200),(3600000,2440000),
    (5003999,3560000),(6599999,4836800),(6600000,4840000),
    (8500000,6550000),
])
def test_nta_2026_salary_table(salary,income):
    assert calculate_salary_income(salary,load_rates()) == income


@pytest.mark.parametrize('salary,income',[(650999,0),(651000,1000),(1899999,1249999),(1900000,1250000),(1903999,1250000),(2000000,1320000)])
def test_local_2026_uses_2025_salary_table(salary,income):
    assert calculate_salary_income(salary,load_rates(),income_year=2025) == income


@pytest.mark.parametrize('income,deduction',[(4890000,1040000),(4890001,670000),(6550000,670000),(6550001,620000)])
def test_nta_2026_basic_deduction_boundary(income,deduction):
    assert _find_basic_deduction(income,load_rates()['income_tax']['basic_deduction_brackets']) == deduction


def test_nta_worked_tax_example_680000_taxable():
    # NTA's 2026 example: 3.56m income minus 1.04m basic and 1.84m other deductions.
    assert calculate_income_tax(3560000,1840000,load_rates()) == (34700,680000)


@pytest.mark.parametrize('region,expected',[('tokyo',102500),('osaka',102800),('kanagawa',103900)])
def test_adjustment_uses_old_system_50000_not_new_income_tax_difference(region,expected):
    r=load_rates(prefecture_code=region)
    # Taxable 1m; credit total2500, separate municipality/prefecture rounding.
    assert calculate_resident_tax(1430000,0,r) == (expected,1000000)
    changed=deepcopy(r);changed['income_tax']['basic_deduction_brackets'][0]['deduction']=9999999
    assert calculate_resident_tax(1430000,0,changed)==(expected,1000000)


def test_yokohama_official_example_at_taxable_2437000():
    # The city's worked example has extra family deductions; direct input produces its same tax base.
    assert calculate_resident_tax(3960000,1093000,load_rates(prefecture_code='kanagawa'))==(247900,2437000)


def test_tokyo_separate_rounding_2372000():
    # 142320-1500=140820 ->140800; 94880-1000=93880 ->93800; +5000.
    assert calculate_resident_tax(3560000,757336,load_rates())==(239600,2372000)


def test_osaka_combined_health_care_half_yen():
    # Official 110000 standard: health5571.5, combined6462.5 -> 5571 and6462.
    x=calculate_social_insurance(110000*12,load_rates(prefecture_code='osaka'))
    assert x.health_employee==5571*12
    assert x.health_employee+x.care_employee==6462*12
    assert x.health_employee+x.care_employee+x.health_employer+x.care_employer==12925*12


def test_tokyo_combined_health_care_at_standard_170000():
    # Official combined half 9749.5 ->9749, never Python bankers rounding to9750.
    x=calculate_social_insurance(170000*12,load_rates())
    assert x.health_employee+x.care_employee==9749*12
