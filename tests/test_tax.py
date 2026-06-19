from src.calculators.income_tax import calculate_income_tax
from src.calculators.resident_tax import calculate_resident_tax
from src.services.rate_loader import load_rates


def test_income_tax_returns_tax_and_taxable_income():
    rates = load_rates()

    tax, taxable_income = calculate_income_tax(3_560_000, 750_000, rates)

    assert taxable_income == 2_130_000
    assert tax == 117_925


def test_income_tax_uses_2026_basic_deduction_table_for_500_man_yen_case():
    rates = load_rates()

    tax, taxable_income = calculate_income_tax(3_560_000, 757_336, rates)

    assert taxable_income == 2_122_000
    assert tax == 117_109


def test_income_tax_uses_low_income_basic_deduction_band():
    rates = load_rates()

    tax, taxable_income = calculate_income_tax(1_320_000, 313_648, rates)

    assert taxable_income == 56_000
    assert tax == 2_859


def test_resident_tax_returns_tax_and_taxable_income():
    rates = load_rates()

    tax, taxable_income = calculate_resident_tax(3_560_000, 750_000, rates)

    assert taxable_income == 2_380_000
    assert tax == 240_500


def test_resident_tax_applies_adjustment_deduction_for_500_man_yen_case():
    rates = load_rates()

    tax, taxable_income = calculate_resident_tax(3_560_000, 757_336, rates)

    assert taxable_income == 2_372_000
    assert tax == 239_700


def test_resident_tax_uses_tokyo_23_wards_non_taxable_threshold():
    rates = load_rates()

    tax, taxable_income = calculate_resident_tax(450_000, 0, rates)

    assert taxable_income == 0
    assert tax == 0


def test_resident_tax_rounds_taxable_income_and_final_tax_down():
    rates = load_rates()

    tax, taxable_income = calculate_resident_tax(451_000, 0, rates)

    assert taxable_income == 21_000
    assert tax == 6_000
