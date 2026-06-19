import json

import pytest

from src.services.rate_loader import load_rates


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
