"""
KPI-specific qualitative context generators.

Rules:
- NO numbers in output
- NO causality ("because", "due to", etc.)
- NO cross-metric references
- Deterministic text only
"""

from typing import List


def _direction(current: float, previous: float | None, flat_threshold: float) -> str:
    if previous is None:
        return "has no prior period available for comparison"

    if previous == 0:
        return "changed compared to the previous period"

    change_pct = (current - previous) / previous

    if abs(change_pct) < flat_threshold:
        return "remained relatively stable compared to the previous period"
    elif change_pct > 0:
        return "increased compared to the previous period"
    else:
        return "declined compared to the previous period"


def _trend(values: List[float]) -> str:
    if len(values) < 3:
        return "has insufficient history to assess short-term trend"

    diffs = [values[i] - values[i - 1] for i in range(1, len(values))]

    if all(d > 0 for d in diffs):
        return "shows a short-term improving trend"
    elif all(d < 0 for d in diffs):
        return "shows a short-term declining trend"
    else:
        return "shows moderate short-term volatility"


# ------------------------------------------------------------
# KPI CONTEXT GENERATORS
# ------------------------------------------------------------

def monthly_revenue_context(values: List[float]) -> str:
    current = values[-1]
    previous = values[-2] if len(values) > 1 else None

    direction = _direction(current, previous, flat_threshold=0.03)
    trend = _trend(values[-3:])

    return (
        "Revenue context (monthly): "
        f"Revenue {direction}. "
        f"Recent performance {trend}."
    )


def monthly_ebitda_context(values: List[float]) -> str:
    current = values[-1]
    previous = values[-2] if len(values) > 1 else None

    direction = _direction(current, previous, flat_threshold=0.05)
    trend = _trend(values[-3:])

    return (
        "EBITDA context (monthly): "
        f"EBITDA {direction}. "
        f"Recent performance {trend}."
    )


def monthly_cash_balance_context(values: List[float]) -> str:
    current = values[-1]
    previous = values[-2] if len(values) > 1 else None

    direction = _direction(current, previous, flat_threshold=0.02)
    trend = _trend(values[-3:])

    return (
        "Cash balance context (monthly): "
        f"Cash balance {direction}. "
        f"Recent performance {trend}."
    )
