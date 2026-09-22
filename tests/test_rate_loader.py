import json

import pytest

from src.services.prefecture_rate_loader import get_supported_prefectures, load_rates


def test_supported_prefectures_contains_tokyo_osaka_and_kanagawa():
    prefectures = get_supported_prefectures()

    assert [(item.code, item.display_name) for item in prefectures] == [
        ("tokyo", "東京都"),
        ("osaka", "大阪府"),
        ("kanagawa", "神奈川県（横浜市想定）"),
        ("fukuoka", "福岡市（協会けんぽ福岡支部）"),
        ("chiba", "千葉市（協会けんぽ千葉支部）"),
        ("saitama", "さいたま市（協会けんぽ埼玉支部）"),
        ("sapporo", "札幌市（協会けんぽ北海道支部）"),
        ("sendai", "仙台市（協会けんぽ宮城支部）"),
        ("niigata", "新潟市（協会けんぽ新潟支部）"),
        ("hiroshima", "広島市（協会けんぽ広島支部）"),
        ("takamatsu", "高松市（協会けんぽ香川支部）"),
        ("kanazawa", "金沢市（協会けんぽ石川支部）"),
        ("shizuoka", "静岡市（協会けんぽ静岡支部）"),
        ("kyoto", "京都市（協会けんぽ京都支部）"),
        ("kobe", "神戸市（協会けんぽ兵庫支部）"),
        ("nagano", "長野市（協会けんぽ長野支部）"),
        ("okayama", "岡山市（協会けんぽ岡山支部）"),
        ("kumamoto", "熊本市（協会けんぽ熊本支部）"),
        ("naha", "那覇市（協会けんぽ沖縄支部）"),
        ("matsuyama", "松山市（協会けんぽ愛媛支部）"),
        ("morioka", "盛岡市（協会けんぽ岩手支部）"),
    ]
    assert prefectures[0].rate_file.name == "rates_2026_tokyo.json"
    assert prefectures[1].rate_file.name == "rates_2026_osaka.json"
    assert prefectures[2].rate_file.name == "rates_2026_kanagawa.json"


def test_load_rates_selects_tokyo_and_marks_prefecture_dependent_fields():
    rates = load_rates(prefecture_code="tokyo")

    assert rates["metadata"]["prefecture"] == "東京都"
    assert rates["regional_scope"] == {
        "prefecture_code": "tokyo",
        "prefecture_name": "東京都",
        "prefecture_dependent_fields": [
            "social_insurance.health_insurance_rate",
            "resident_tax",
        ],
    }
    assert rates["social_insurance"]["health_insurance_rate"] == 0.0985


def test_load_rates_selects_osaka_and_inherits_common_settings():
    rates = load_rates(prefecture_code="osaka")

    assert rates["metadata"]["prefecture"] == "大阪府"
    assert rates["regional_scope"]["prefecture_code"] == "osaka"
    assert rates["social_insurance"]["health_insurance_rate"] == 0.1013
    assert rates["social_insurance"]["care_insurance_rate"] == 0.0162
    assert rates["social_insurance"]["pension_rate"] == 0.183
    assert rates["resident_tax"]["municipality_class"] == "osaka_city"
    assert rates["resident_tax"]["per_capita"] == 4300
    assert rates["income_tax"] == load_rates(prefecture_code="tokyo")["income_tax"]


def test_load_rates_rejects_unsupported_prefecture():
    with pytest.raises(ValueError, match="Unsupported prefecture_code: aichi"):
        load_rates(prefecture_code="aichi")


def test_load_rates_requires_income_tax_basic_deduction_brackets(tmp_path):
    rates = {
        "income_tax": {
            "basic_deduction": 480_000,
            "reconstruction_surtax_rate": 0.021,
            "brackets": [],
        }
    }
    rate_file = tmp_path / "rates_missing_basic_deduction_brackets.json"
    rate_file.write_text(json.dumps(rates), encoding="utf-8")

    with pytest.raises(ValueError, match="income_tax.basic_deduction_brackets is required"):
        load_rates(rate_file)
