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
    assert result.insurance.employee_total == 762_988
    assert result.tax.income_tax == 116_500
    assert result.tax.resident_tax == 239_200
    assert result.tax.total == 355_700
    assert result.insurance.employer_total == 798_212
    assert result.annual_take_home == 3_881_312
    assert result.monthly_take_home_average == 323_443
    assert result.total_labor_cost == 5_798_212
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
        (2_000_000, 315_988, 39_100, 1_644_912, 137_076, 330_344, 2_330_344),
        (3_000_000, 483_000, 126_700, 2_390_300, 199_192, 504_732, 3_504_732),
        (4_000_000, 632_000, 216_000, 3_152_000, 262_667, 660_688, 4_660_688),
        (5_000_000, 762_988, 355_700, 3_881_312, 323_443, 798_212, 5_798_212),
        (6_000_000, 930_000, 483_700, 4_586_300, 382_192, 972_600, 6_972_600),
        (7_000_000, 1_097_000, 642_500, 5_260_500, 438_375, 1_147_000, 8_147_000),
        (8_000_000, 1_231_060, 875_200, 5_893_740, 491_145, 1_287_140, 9_287_140),
        (9_000_000, 1_285_200, 1_157_900, 6_556_900, 546_408, 1_344_792, 10_344_792),
        (10_000_000, 1_346_360, 1_443_600, 7_210_040, 600_837, 1_409_452, 11_409_452),
    ]


def test_osaka_simulation_uses_osaka_health_rate_and_resident_tax_settings():
    rates = load_rates(prefecture_code="osaka")
    result = simulate_annual_salary(5_000_000, rates)

    assert result.insurance.health_standard_monthly == 410_000
    assert result.insurance.health_employee == 249_192
    assert result.insurance.care_employee == 39_852
    assert result.insurance.pension_employee == 450_180
    assert result.insurance.employment_employee == 25_000
    assert result.insurance.employee_total == 769_876
    assert result.tax.income_tax == 115_800
    assert result.tax.resident_tax == 238_800
    assert result.insurance.employer_total == 805_100
    assert result.annual_take_home == 3_875_524
    assert result.monthly_take_home_average == 322_960
    assert result.total_labor_cost == 5_805_100
