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
# These are ONLY raw, ingestible fields.
# -------------------------------------------------------------------
CANONICAL_FIELDS: List[CanonicalField] = [

    # -----------------------------
    # TIME
    # -----------------------------
    CanonicalField(
    name="period_date",
    required=True,
    data_type="date",
    aliases=[
        "date",
        "month",
        "period",
        "period end",
        "period_date",
    ],
),


    # -----------------------------
    # P&L — RAW
    # -----------------------------
    CanonicalField(
        name="revenue",
        required=False,
        data_type="numeric",
        aliases=[
            "revenue",
            "total revenue",
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
            "operating profit",
            "operating income",
        ],
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
        name="marketing_expense",
        required=False,
        data_type="numeric",
        aliases=[
            "marketing expense",
            "marketing spend",
            "ads spend",
            "advertising cost",
        ],
    ),
    CanonicalField(
        name="fulfillment_expense",
        required=False,
        data_type="numeric",
        aliases=[
            "fulfillment expense",
            "shipping cost",
            "delivery cost",
            "logistics cost",
        ],
    ),

    # -----------------------------
    # CASH / BALANCE SHEET — RAW
    # -----------------------------
    CanonicalField(
        name="cash_balance",
        required=False,
        data_type="numeric",
        aliases=[
            "cash balance",
            "cash",
            "closing cash",
            "ending cash",
            "bank balance",
            "cash on hand",
        ],
    ),

    # -----------------------------
    # UNIT ECONOMICS INPUTS — RAW
    # -----------------------------
    CanonicalField(
        name="orders",
        required=False,
        data_type="numeric",
        aliases=[
            "orders",
            "total orders",
            "number of orders",
            "order count",
        ],
    ),
    CanonicalField(
        name="customers",
        required=False,
        data_type="numeric",
        aliases=[
            "customers",
            "unique customers",
            "active customers",
        ],
    ),

    # -----------------------------
    # MIX / DIMENSIONS — RAW
    # -----------------------------
    CanonicalField(
        name="customer_type",
        required=False,
        data_type="string",
        aliases=[
            "customer type",
            "customer segment",
            "customer category",
        ],
    ),
    CanonicalField(
        name="channel",
        required=False,
        data_type="string",
        aliases=[
            "channel",
            "sales channel",
            "acquisition channel",
        ],
    ),
    CanonicalField(
        name="product",
        required=False,
        data_type="string",
        aliases=[
            "product",
            "sku",
            "product name",
        ],
    ),
    CanonicalField(
        name="geo",
        required=False,
        data_type="string",
        aliases=[
            "country",
            "region",
            "geography",
            "market",
        ],
    ),
]


# -------------------------------------------------------------------
# Lookup Helpers
# -------------------------------------------------------------------
CANONICAL_FIELD_BY_NAME: Dict[str, CanonicalField] = {
    field.name: field for field in CANONICAL_FIELDS
}

CANONICAL_FIELD_NAMES: Set[str] = set(CANONICAL_FIELD_BY_NAME.keys())


# -------------------------------------------------------------------
# SOFT METRIC EXPECTATIONS (NOT ENFORCED)
# These include DERIVED metrics — correct by design.
# -------------------------------------------------------------------

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
        "runway_months",
    },
    "balance_sheet": {
        "total_assets",
        "total_liabilities",
        "equity",
        "working_capital",
    },
    "unit_economics": {
        "aov",
        "repeat_order_rate",
        "contribution_margin",
    },
}


EXPECTED_METRICS_BY_INDUSTRY = {
    "d2c": {
        "pnl": {
            "marketing_expense",
            "fulfillment_expense",
        },
        "balance_sheet": {
            "inventory",
            "accounts_payable",
        },
        "unit_economics": {
            "customer_mix",
            "channel_mix",
            "product_mix",
        },
    }
}
