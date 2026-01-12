# app/orchestration/router.py

from typing import List, Dict

from app.agents.revenue_agent import handle_revenue_query
from app.agents.expense_agent import handle_expense_query
from app.agents.cash_agent import handle_cash_query
from app.agents.kpi_agent import handle_kpi_query


INTENT_TO_HANDLER = {
    "revenue": handle_revenue_query,
    "expenses": handle_expense_query,
    "cash": handle_cash_query,
    "kpis": handle_kpi_query,
}


def route_intents(
    intents: List[Dict],
    context: Dict
) -> List[Dict]:
    """
    Routes detected intents to corresponding domain agents.

    Args:
        intents: list of {"intent": str, "confidence": float}
        context: shared context (query, company_id, period, etc.)

    Returns:
        List of domain agent responses
    """
    responses = []

    for intent_obj in intents:
        intent = intent_obj["intent"]
        confidence = intent_obj["confidence"]

        # Skip low-confidence intents
        if confidence < 0.6:
            continue

        handler = INTENT_TO_HANDLER.get(intent)

        if not handler:
            continue

        response = handler({
            **context,
            "confidence": confidence
        })

        responses.append(response)

    return responses
