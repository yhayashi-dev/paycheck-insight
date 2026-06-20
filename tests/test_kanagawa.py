from src.services.prefecture_rate_loader import load_rates
from src.services.simulation import simulate_annual_salary


def test_kanagawa_rates_use_yokohama_scope_and_official_sources():
    rates = load_rates(prefecture_code="kanagawa")

    assert rates["metadata"]["prefecture"] == "神奈川県（横浜市想定）"
    assert rates["regional_scope"]["prefecture_code"] == "kanagawa"
    assert rates["social_insurance"]["health_insurance_rate"] == 0.0992
    assert rates["social_insurance"]["care_insurance_rate"] == 0.0162
    assert rates["social_insurance"]["pension_rate"] == 0.183
    assert rates["resident_tax"]["municipality_class"] == "yokohama_city"
    assert rates["resident_tax"]["income_rate"] == 0.10025
    assert rates["resident_tax"]["per_capita"] == 5_200
    assert rates["resident_tax"]["forest_environment_tax"] == 1_000
    assert any(
        item["item"] == "健康保険料率"
        and item["source_url"].endswith("R8_14kanagawa.pdf")
        for item in rates["social_insurance"]["verification"]
    )
    assert any(
        item["item"] == "非課税判定（横浜市）"
        and item["source_url"].startswith("https://www.city.yokohama.lg.jp/")
        for item in rates["resident_tax"]["verification"]
    )


def test_kanagawa_500_man_yen_simulation_matches_expected_values():
    result = simulate_annual_salary(
        5_000_000,
        load_rates(prefecture_code="kanagawa"),
    )

    assert result.insurance.health_standard_monthly == 410_000
    assert result.insurance.health_employee == 244_032
    assert result.insurance.employee_total == 759_064
    assert result.tax.income_tax == 116_904
    assert result.tax.resident_tax == 241_200
    assert result.tax.total == 358_104
    assert result.insurance.employer_total == 794_276
    assert result.annual_take_home == 3_882_832
    assert result.monthly_take_home_average == 323_569
    assert result.total_labor_cost == 5_794_276


def test_app_comparison_includes_kanagawa_and_preserves_existing_results():
    import app

    comparison_results = [
        (
            display_name,
            simulate_annual_salary(5_000_000, app.get_rates(code)),
        )
        for code, display_name in [
            ("tokyo", "東京都"),
            ("osaka", "大阪府"),
            ("kanagawa", "神奈川県（横浜市想定）"),
        ]
    ]

    html = app.prefecture_comparison_html(comparison_results)

    assert html.count('class="comparison-prefecture-card"') == 3
    assert "3,885,855円" in html
    assert "3,880,082円" in html
    assert "3,882,832円" in html
    assert "差額（神奈川県（横浜市想定） − 東京都）" in html
    assert "神奈川県（横浜市想定）は東京都より " in html
    assert '<span class="comparison-difference-value">-3,023円</span>' in html
