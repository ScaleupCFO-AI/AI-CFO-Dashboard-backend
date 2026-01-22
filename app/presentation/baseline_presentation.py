from app.retrieval.retrieve_company_summaries import retrieve_company_summaries
from app.presentation.presentation_builder import build_presentation
from app.presentation.presentation_schema import PresentationIntent, MetricIntent
from app.presentation.chart_intents import ChartIntent


def get_company_baseline(company_id: str) -> dict:
    """
    Deterministic baseline dashboard presentation.
    Uses SAME chart builder as /query.
    No LLM.
    """

    # 1️⃣ Get summaries (same source as /query)
    summaries = retrieve_company_summaries(company_id)

    # 2️⃣ Define baseline intent deterministically
    baseline_intent = PresentationIntent(
        main=[
            MetricIntent(metric="revenue", intent=ChartIntent.TREND),
            MetricIntent(metric="gross_margin", intent=ChartIntent.TREND),
            MetricIntent(metric="cash_balance", intent=ChartIntent.TREND),
        ],
        first_degree=[],
        second_degree=[
            MetricIntent(metric="customer_mix", intent=ChartIntent.CONTRIBUTION),
            MetricIntent(metric="channel_mix", intent=ChartIntent.CONTRIBUTION),
            MetricIntent(metric="product_mix", intent=ChartIntent.CONTRIBUTION),
        ],
    )

    # 3️⃣ Build charts using the SAME logic as /query
    presentation = build_presentation(
        presentation_intent=baseline_intent,
        summaries=summaries,
    )

    return presentation
