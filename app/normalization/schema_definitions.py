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
    CanonicalField(
    name="cash_balance",
    required=False,
    data_type="numeric",
    aliases=[
        "cash_balance",
        "cash",
        "closing_cash",
        "ending_cash",
        "bank_balance",
    ],
    ),
    CanonicalField(
        name="cash_balance",
        required=False,
        data_type="numeric",
        aliases=["cash balance", "ending cash", "closing cash"]
    ),

    CanonicalField(
        name="operating_expense",
        required=False,
        data_type="numeric",
        aliases=["opex", "operating expense", "operating expenses"]
    ),

    CanonicalField(
        name="net_profit",
        required=False,
        data_type="numeric",
        aliases=["net profit", "profit after tax", "net income"]
    ),
    CanonicalField(
    name="operating_expense",
    required=False,
    data_type="numeric",
    aliases=[
        "operating expense",
        "operating expenses",
        "opex",
        "operating cost",
        "operating costs",
    ],
),
    CanonicalField(
    name="net_profit",
    required=False,
    data_type="numeric",
    aliases=[
        "net profit",
        "profit",
        "net income",
        "earnings",
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
        "cogs",
        "gross_margin",
        "operating_expense",
        "ebitda",
        "net_profit",
    },
    "cash_flow": {
        "cash_balance",
        "operating_cash_flow",
        "burn_rate",
        "runway",
    },
    "balance_sheet": {
        "total_assets",
        "total_liabilities",
        "equity",
        "working_capital",
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
