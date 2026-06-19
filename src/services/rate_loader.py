"""Backward-compatible imports for the prefecture-aware rate loader."""

from src.services.prefecture_rate_loader import (
    DEFAULT_PREFECTURE_CODE,
    DEFAULT_RATE_FILE,
    PREFECTURE_RATE_CONFIGS,
    PrefectureRateConfig,
    get_supported_prefectures,
    load_rates,
)

__all__ = [
    "DEFAULT_PREFECTURE_CODE",
    "DEFAULT_RATE_FILE",
    "PREFECTURE_RATE_CONFIGS",
    "PrefectureRateConfig",
    "get_supported_prefectures",
    "load_rates",
]
