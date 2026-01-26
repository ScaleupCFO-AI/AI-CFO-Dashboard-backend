from app.retrieval.retrieve_company_summaries import retrieve_company_summaries
from app.presentation.presentation_builder import build_presentation
from app.presentation.presentation_schema import PresentationIntent
from app.presentation.chart_intents import ChartIntent
from app.db.connection import get_db_connection


def get_company_baseline(company_id: str) -> dict:
    """
    Deterministic baseline dashboard presentation.

    - NO LLM
    - Same chart builder as /query
    - Root KPIs are fixed
    - Supporting KPIs are derived via metric_dependencies
    """

    # 1️⃣ Get summaries
    summaries = retrieve_company_summaries(company_id)

    # 2️⃣ Define baseline ROOT KPIs
    baseline_intent = PresentationIntent(
        root_kpis=[
            "revenue",
            "gross_margin",
            "cash_balance",
        ],
        intent=ChartIntent.TREND.value,  # ensure string enum
        time_scope=None
    )

    # 3️⃣ Open DB connection
    conn = get_db_connection()

    try:
        presentation = build_presentation(
            presentation_intent=baseline_intent,
            summaries=summaries,
            db_conn=conn
        )
    finally:
        conn.close()

    return presentation
