from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_RATE_FILE = Path(__file__).resolve().parents[2] / "data" / "rates_2026_tokyo.json"


def load_rates(path: Path | None = None) -> dict[str, Any]:
    """Load tax and social-insurance rates from a single JSON settings file."""

    rate_file = path or DEFAULT_RATE_FILE
    with rate_file.open(encoding="utf-8") as file:
        rates = json.load(file)

    _validate_rates(rates, rate_file)
    return rates


def _validate_rates(rates: dict[str, Any], rate_file: Path) -> None:
    income_tax = rates.get("income_tax")
    if not isinstance(income_tax, dict):
        raise ValueError(f"{rate_file} must define income_tax settings.")

    if "basic_deduction_brackets" not in income_tax:
        raise ValueError(
            f"{rate_file} income_tax.basic_deduction_brackets is required. "
            "The 2026 income-tax basic deduction must be configured as income-based brackets."
        )

    brackets = income_tax["basic_deduction_brackets"]
    if not isinstance(brackets, list) or not brackets:
        raise ValueError(f"{rate_file} income_tax.basic_deduction_brackets must be a non-empty list.")

    for index, bracket in enumerate(brackets):
        if not isinstance(bracket, dict) or "upper" not in bracket or "deduction" not in bracket:
            raise ValueError(
                f"{rate_file} income_tax.basic_deduction_brackets[{index}] "
                "must define upper and deduction."
            )
