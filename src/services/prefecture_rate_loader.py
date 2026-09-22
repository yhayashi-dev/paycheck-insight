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
    "kanagawa": PrefectureRateConfig(
        code="kanagawa",
        display_name="神奈川県（横浜市想定）",
        rate_file=DATA_DIR / "rates_2026_kanagawa.json",
    ),
    "fukuoka": PrefectureRateConfig(
        code="fukuoka",
        display_name="福岡市（協会けんぽ福岡支部）",
        rate_file=DATA_DIR / "rates_2026_fukuoka.json",
    ),
    "chiba": PrefectureRateConfig(code="chiba", display_name="千葉市（協会けんぽ千葉支部）", rate_file=DATA_DIR / "rates_2026_chiba.json"),
    "saitama": PrefectureRateConfig(code="saitama", display_name="さいたま市（協会けんぽ埼玉支部）", rate_file=DATA_DIR / "rates_2026_saitama.json"),
    "sapporo": PrefectureRateConfig(code="sapporo", display_name="札幌市（協会けんぽ北海道支部）", rate_file=DATA_DIR / "rates_2026_sapporo.json"),
    "sendai": PrefectureRateConfig(code="sendai", display_name="仙台市（協会けんぽ宮城支部）", rate_file=DATA_DIR / "rates_2026_sendai.json"),
    "niigata": PrefectureRateConfig(code="niigata", display_name="新潟市（協会けんぽ新潟支部）", rate_file=DATA_DIR / "rates_2026_niigata.json"),
    "hiroshima": PrefectureRateConfig(code="hiroshima", display_name="広島市（協会けんぽ広島支部）", rate_file=DATA_DIR / "rates_2026_hiroshima.json"),
    "takamatsu": PrefectureRateConfig(code="takamatsu", display_name="高松市（協会けんぽ香川支部）", rate_file=DATA_DIR / "rates_2026_takamatsu.json"),
    "kanazawa": PrefectureRateConfig(code="kanazawa", display_name="金沢市（協会けんぽ石川支部）", rate_file=DATA_DIR / "rates_2026_kanazawa.json"),
    "shizuoka": PrefectureRateConfig(code="shizuoka", display_name="静岡市（協会けんぽ静岡支部）", rate_file=DATA_DIR / "rates_2026_shizuoka.json"),
    "kyoto": PrefectureRateConfig(code="kyoto", display_name="京都市（協会けんぽ京都支部）", rate_file=DATA_DIR / "rates_2026_kyoto.json"),
    "kobe": PrefectureRateConfig(code="kobe", display_name="神戸市（協会けんぽ兵庫支部）", rate_file=DATA_DIR / "rates_2026_kobe.json"),
    "nagano": PrefectureRateConfig(code="nagano", display_name="長野市（協会けんぽ長野支部）", rate_file=DATA_DIR / "rates_2026_nagano.json"),
    "okayama": PrefectureRateConfig(code="okayama", display_name="岡山市（協会けんぽ岡山支部）", rate_file=DATA_DIR / "rates_2026_okayama.json"),
    "kumamoto": PrefectureRateConfig(code="kumamoto", display_name="熊本市（協会けんぽ熊本支部）", rate_file=DATA_DIR / "rates_2026_kumamoto.json"),
    "naha": PrefectureRateConfig(code="naha", display_name="那覇市（協会けんぽ沖縄支部）", rate_file=DATA_DIR / "rates_2026_naha.json"),
    "matsuyama": PrefectureRateConfig(code="matsuyama", display_name="松山市（協会けんぽ愛媛支部）", rate_file=DATA_DIR / "rates_2026_matsuyama.json"),
    "morioka": PrefectureRateConfig(code="morioka", display_name="盛岡市（協会けんぽ岩手支部）", rate_file=DATA_DIR / "rates_2026_morioka.json"),
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

    if rates.get("schema_version") == 1 and "calculation_context" in rates:
        from src.services.period_settings import CalculationContext, load_calculation_rates
        result = load_calculation_rates(
            CalculationContext(**rates["calculation_context"]),
            assumptions=rates["assumptions"],
        )
        result["metadata"].update(rates["metadata"])
        result["regional_scope"] = rates["regional_scope"]
        return result
    if "extends" in rates:
        raise ValueError("Regional inheritance is no longer supported; use an explicit preset")
    return rates


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
