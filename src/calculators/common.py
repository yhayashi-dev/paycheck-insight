from __future__ import annotations


def round_down_to_unit(value: float, unit: int) -> int:
    """Round positive yen amounts down to the configured unit."""

    if unit <= 1:
        return int(value)
    return int(value // unit * unit)


def yen(value: float) -> int:
    """Convert a calculated yen amount to an integer yen amount."""

    return int(round(value))
