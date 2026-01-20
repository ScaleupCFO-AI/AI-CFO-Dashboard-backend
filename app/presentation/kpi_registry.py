STATEMENT_KPIS = {
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

"""
Metric proxy registry.

Rules:
- Proxies must belong to the SAME statement
- Proxies must represent the SAME financial concept
- Order matters: first available proxy is used
"""

METRIC_PROXIES = {
    # ────────────── CASH FLOW / LIQUIDITY ──────────────
    "runway": [
        "cash_balance"
    ],

    "burn_rate": [
        "operating_cash_flow"
    ],

    "operating_cash_flow": [
        "cash_balance"
    ],

    # ────────────── PROFITABILITY (P&L) ──────────────
    "net_profit": [
        "ebitda"
    ],

    "ebitda": [
        "gross_margin"
    ],

    "gross_margin": [
        "cogs",
        "revenue"
    ],

    # ────────────── GROWTH ──────────────
    "revenue_growth": [
        "revenue"
    ],
}
