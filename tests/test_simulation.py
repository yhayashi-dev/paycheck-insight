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
    assert result.tax.income_tax == 89_600
    assert result.tax.resident_tax == 239_100
    assert result.tax.total == 328_700
    assert result.insurance.employer_total == 798_224
    assert result.annual_take_home == 3_908_312
    assert result.monthly_take_home_average == 325_693
    assert result.total_labor_cost == 5_798_224
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
        (2000000, 315988, 59800, 1624212, 135351, 330356, 2330356),
        (3000000, 483000, 138400, 2378600, 198217, 504732, 3504732),
        (4000000, 632000, 227700, 3140300, 261692, 660688, 4660688),
        (5000000, 762988, 328700, 3908312, 325693, 798224, 5798224),
        (6000000, 930000, 446900, 4623100, 385258, 972600, 6972600),
        (7000000, 1096988, 634200, 5268812, 439068, 1147000, 8147000),
        (8000000, 1231060, 866900, 5902040, 491837, 1287140, 9287140),
        (9000000, 1285188, 1149700, 6565112, 547093, 1344792, 10344792),
        (10000000, 1346348, 1435300, 7218352, 601529, 1409452, 11409452),
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
    assert result.tax.income_tax == 89_300
    assert result.tax.resident_tax == 238_800
    assert result.insurance.employer_total == 805_112
    assert result.annual_take_home == 3_902_024
    assert result.monthly_take_home_average == 325_169
    assert result.total_labor_cost == 5_805_112
