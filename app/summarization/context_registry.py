"""
Registry defining which KPIs receive contextual summaries
and which generator is responsible for each.
"""

from app.summarization.kpi_context import (
    monthly_revenue_context,
    monthly_ebitda_context,
    monthly_cash_balance_context,
)

MONTHLY_CONTEXT_REGISTRY = {
    "revenue": {
        "summary_type": "monthly_revenue_context",
        "generator": monthly_revenue_context,
    },
    "ebitda": {
        "summary_type": "monthly_ebitda_context",
        "generator": monthly_ebitda_context,
    },
    "cash_balance": {
        "summary_type": "monthly_cash_balance_context",
        "generator": monthly_cash_balance_context,
    },
}
