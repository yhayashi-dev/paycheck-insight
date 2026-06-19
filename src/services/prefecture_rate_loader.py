from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DEFAULT_PREFECTURE_CODE = "tokyo"


@dataclass(frozen=True)
class PrefectureRateConfig:
    """One supported prefecture and its rate settings file."""

    code: str
    display_name: str
    rate_file: Path


PREFECTURE_RATE_CONFIGS = {
    "tokyo": PrefectureRateConfig(
        code="tokyo",
        display_name="東京都",
        rate_file=DATA_DIR / "rates_2026_tokyo.json",
    ),
    "osaka": PrefectureRateConfig(
        code="osaka",
        display_name="大阪府",
        rate_file=DATA_DIR / "rates_2026_osaka.json",
    ),
}
DEFAULT_RATE_FILE = PREFECTURE_RATE_CONFIGS[DEFAULT_PREFECTURE_CODE].rate_file


def get_supported_prefectures() -> tuple[PrefectureRateConfig, ...]:
    """Return supported prefectures in UI display order."""

    return tuple(PREFECTURE_RATE_CONFIGS.values())


def load_rates(
    path: Path | None = None,
    *,
    prefecture_code: str = DEFAULT_PREFECTURE_CODE,
) -> dict[str, Any]:
    """Load rates for a supported prefecture or an explicit settings file."""

    prefecture_config = PREFECTURE_RATE_CONFIGS.get(prefecture_code)
    if prefecture_config is None:
        supported = ", ".join(PREFECTURE_RATE_CONFIGS)
        raise ValueError(
            f"Unsupported prefecture_code: {prefecture_code}. Supported values: {supported}."
        )

    rate_file = path or prefecture_config.rate_file
    rates = _load_rate_file(rate_file)

    _validate_rates(rates, rate_file)
    if path is None:
        _validate_prefecture_scope(rates, rate_file, prefecture_config)
    return rates


def _load_rate_file(rate_file: Path, loading: frozenset[Path] = frozenset()) -> dict[str, Any]:
    resolved_file = rate_file.resolve()
    if resolved_file in loading:
        raise ValueError(f"Circular rate-file inheritance detected at {rate_file}.")

    with rate_file.open(encoding="utf-8") as file:
        rates = json.load(file)

    parent_name = rates.pop("extends", None)
    if parent_name is None:
        return rates
    if not isinstance(parent_name, str) or Path(parent_name).name != parent_name:
        raise ValueError(f"{rate_file} extends must name a JSON file in the same directory.")

    parent_file = rate_file.parent / parent_name
    parent_rates = _load_rate_file(parent_file, loading | {resolved_file})
    return _deep_merge(parent_rates, rates)


def _deep_merge(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _validate_prefecture_scope(
    rates: dict[str, Any],
    rate_file: Path,
    prefecture_config: PrefectureRateConfig,
) -> None:
    scope = rates.get("regional_scope")
    if not isinstance(scope, dict):
        raise ValueError(f"{rate_file} must define regional_scope settings.")

    if scope.get("prefecture_code") != prefecture_config.code:
        raise ValueError(
            f"{rate_file} regional_scope.prefecture_code must be "
            f"{prefecture_config.code!r}."
        )

    if scope.get("prefecture_name") != prefecture_config.display_name:
        raise ValueError(
            f"{rate_file} regional_scope.prefecture_name must be "
            f"{prefecture_config.display_name!r}."
        )

    regional_fields = scope.get("prefecture_dependent_fields")
    if not isinstance(regional_fields, list) or not regional_fields:
        raise ValueError(
            f"{rate_file} regional_scope.prefecture_dependent_fields "
            "must be a non-empty list."
        )


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
