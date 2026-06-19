from src.services.simulation import simulate_annual_salary


def test_app_get_rates_loads_default_rates_for_500_man_yen_case():
    import app

    rates = app.get_rates("tokyo")
    result = simulate_annual_salary(5_000_000, rates)

    assert rates["income_tax"]["basic_deduction_brackets"][2]["deduction"] == 680_000
    assert result.salary_income == 3_560_000
    assert result.tax.taxable_income_for_income_tax == 2_122_000
    assert result.tax.income_tax == 117_109
    assert result.tax.taxable_income_for_resident_tax == 2_372_000
    assert result.tax.resident_tax == 239_700
    assert result.insurance.employee_total == 757_336
    assert result.insurance.employer_total == 792_548
    assert result.annual_take_home == 3_885_855
    assert result.monthly_take_home_average == 323_821
    assert result.total_labor_cost == 5_792_548


def test_app_verification_metadata_splits_confirmed_and_unconfirmed_items():
    import app

    rates = app.get_rates("tokyo")
    verified_items, unverified_items = app.collect_verification_items(rates)

    assert rates["metadata"]["provisional"] is True
    assert rates["salary_income_deduction"]["provisional"] is False
    assert rates["income_tax"]["provisional"] is True
    assert rates["resident_tax"]["provisional"] is False
    assert rates["social_insurance"]["provisional"] is True
    assert "一部未確認項目あり" in rates["metadata"]["notice"]

    assert any(item["item"] == "所得税の基礎控除" for item in verified_items)
    assert any(item["item"] == "均等割" for item in verified_items)
    assert any(item["item"] == "所得税額の最終端数処理" for item in unverified_items)
    assert any(item["section"] == "社会保険料" for item in unverified_items)
    assert all("source_name" in item for item in verified_items + unverified_items)
    assert all("applicable_period" in item for item in verified_items + unverified_items)
