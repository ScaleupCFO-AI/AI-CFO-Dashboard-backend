from dataclasses import dataclass
from typing import List, Dict, Set


# -------------------------------------------------------------------
# Canonical Field Definition
# -------------------------------------------------------------------
@dataclass(frozen=True)
class CanonicalField:
    """
    CanonicalField defines a structurally valid column in the system.

    IMPORTANT:
    - required=True means structurally required to interpret the file
    - required=False means optional financial fact
    - required does NOT mean financially mandatory
    """
    name: str
    required: bool
    data_type: str
    aliases: List[str]


# -------------------------------------------------------------------
# Canonical Fields Registry (SINGLE SOURCE OF TRUTH)
# -------------------------------------------------------------------
CANONICAL_FIELDS: List[CanonicalField] = [
    CanonicalField(
        name="period_date",
        required=True,   # cannot ingest without a time dimension
        data_type="date",
        aliases=[
            "date",
            "month",
            "period",
            "period end",
            "period_date",
        ],
    ),
    CanonicalField(
        name="revenue",
        required=False,  # important, but NOT mandatory
        data_type="numeric",
        aliases=[
            "revenue",
            "total revenue",
            "revenue_total",
            "sales",
            "net sales",
            "turnover",
        ],
    ),
    CanonicalField(
        name="cogs",
        required=False,
        data_type="numeric",
        aliases=[
            "cogs",
            "cost of goods sold",
            "cost of sales",
        ],
    ),
    CanonicalField(
        name="ebitda",
        required=False,
        data_type="numeric",
        aliases=[
            "ebitda",
            "ebitda margin",
            "operating profit",
            "operating income",
        ],
    ),
]


# -------------------------------------------------------------------
# Lookup Helpers (used by deterministic mapping logic)
# -------------------------------------------------------------------
CANONICAL_FIELD_BY_NAME: Dict[str, CanonicalField] = {
    field.name: field for field in CANONICAL_FIELDS
}

CANONICAL_FIELD_NAMES: Set[str] = set(CANONICAL_FIELD_BY_NAME.keys())


# -------------------------------------------------------------------
# SOFT METRIC EXPECTATIONS (NOT ENFORCED)
# Used for:
# - validation issues
# - confidence scoring
# - UX transparency
# -------------------------------------------------------------------

# Global expectations (apply to all companies)
EXPECTED_METRICS_GLOBAL = {
    "pnl": {
        "revenue",
        "ebitda",
    },
    "balance_sheet": {
        "cash",
        "total_assets",
        "total_liabilities",
    },
    "cash_flow": {
        "net_cash_flow",
    },
}

# Industry-specific expectations (additive, non-blocking)
EXPECTED_METRICS_BY_INDUSTRY = {
    "d2c": {
        "pnl": {
            "cogs",
            "marketing_expenses",
            "fulfillment_expenses",
        },
        "balance_sheet": {
            "inventory",
            "accounts_payable",
        },
        "cash_flow": {
            "operating_cash_flow",
        },
    }
}
