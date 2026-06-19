from src.services.rate_loader import load_rates
from src.services.simulation import simulate_annual_salary, simulate_salary_range


def test_simulation_calculates_required_output_items():
    rates = load_rates()
    result = simulate_annual_salary(5_000_000, rates)

    assert result.annual_salary == 5_000_000
    assert result.insurance.health_standard_monthly == 410_000
    assert result.insurance.pension_standard_monthly == 410_000
    assert result.insurance.health_employee == 242_304
    assert result.insurance.care_employee == 39_852
    assert result.insurance.pension_employee == 450_180
    assert result.insurance.employment_employee == 25_000
    assert result.insurance.employee_total == 757_336
    assert result.tax.income_tax == 117_109
    assert result.tax.resident_tax == 239_700
    assert result.tax.total == 356_809
    assert result.insurance.employer_total == 792_548
    assert result.annual_take_home == 3_885_855
    assert result.monthly_take_home_average == 323_821
    assert result.total_labor_cost == 5_792_548
    assert result.provisional is True


def test_salary_range_contains_200_to_1000_man_yen():
    rates = load_rates()
    results = simulate_salary_range(rates)

    assert [result.annual_salary for result in results] == [
        2_000_000,
        3_000_000,
        4_000_000,
        5_000_000,
        6_000_000,
        7_000_000,
        8_000_000,
        9_000_000,
        10_000_000,
    ]
    assert [
        (
            result.annual_salary,
            result.insurance.employee_total,
            result.tax.total,
            result.annual_take_home,
            result.monthly_take_home_average,
            result.insurance.employer_total,
            result.total_labor_cost,
        )
        for result in results
    ] == [
        (2_000_000, 313_648, 39_459, 1_646_893, 137_241, 327_992, 2_327_992),
        (3_000_000, 479_412, 127_193, 2_393_395, 199_450, 501_144, 3_501_144),
        (4_000_000, 627_308, 216_615, 3_156_077, 263_006, 655_996, 4_655_996),
        (5_000_000, 757_336, 356_809, 3_885_855, 323_821, 792_548, 5_792_548),
        (6_000_000, 923_100, 484_940, 4_591_960, 382_663, 965_700, 6_965_700),
        (7_000_000, 1_088_864, 644_943, 5_266_193, 438_849, 1_138_852, 8_138_852),
        (8_000_000, 1_221_676, 878_264, 5_900_060, 491_672, 1_277_756, 9_277_756),
        (9_000_000, 1_274_856, 1_161_342, 6_563_802, 546_984, 1_334_436, 10_334_436),
        (10_000_000, 1_334_912, 1_447_289, 7_217_799, 601_483, 1_397_992, 11_397_992),
    ]


def test_osaka_simulation_uses_osaka_health_rate_and_resident_tax_settings():
    rates = load_rates(prefecture_code="osaka")
    result = simulate_annual_salary(5_000_000, rates)

    assert result.insurance.health_standard_monthly == 410_000
    assert result.insurance.health_employee == 249_192
    assert result.insurance.care_employee == 39_852
    assert result.insurance.pension_employee == 450_180
    assert result.insurance.employment_employee == 25_000
    assert result.insurance.employee_total == 764_224
    assert result.tax.income_tax == 116_394
    assert result.tax.resident_tax == 239_300
    assert result.insurance.employer_total == 799_436
    assert result.annual_take_home == 3_880_082
    assert result.monthly_take_home_average == 323_340
    assert result.total_labor_cost == 5_799_436
