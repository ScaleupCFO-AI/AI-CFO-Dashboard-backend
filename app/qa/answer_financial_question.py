import asyncio

from app.retrieval.retrieve_financial_evidence import retrieve_financial_evidence
from app.retrieval.retrieve_evidence_sources_from_summaries import (
    retrieve_evidence_sources_from_summaries,
)

from app.qa.claude_prompt import build_prompt
from app.llm.local_llm import call_llm

from app.contracts.ingestion_quality_contract import reduce_severity
from app.contracts.agent_behaviour_contract import AGENT_BEHAVIOR
from app.contracts.confidence_contract import compute_confidence
from app.contracts.limitations_contract import generate_limitations
from app.contracts.severity import Severity

# Presentation layer
from app.presentation.presentation_llm import call_presentation_llm
from app.presentation.presentation_builder import build_presentation
from app.presentation.statement_resolver import resolve_statements

from app.db.connection import get_db_connection
from app.ingestion.period_derivation import resolve_time_range


async def answer_question(question: str, company_id: str) -> dict:
    """
    Contract-compliant financial question answering.
    """

    # ------------------------------------------------------------
    # 1️⃣ Retrieve evidence (summaries)
    # ------------------------------------------------------------
    evidence = retrieve_financial_evidence(
        question=question,
        company_id=company_id
    )

    evidence = sorted(
        evidence,
        key=lambda x: x.get("period_start") or ""
    )

    # ------------------------------------------------------------
    # 2️⃣ Resolve time range (BEFORE LLM)
    # ------------------------------------------------------------
    start, end = resolve_time_range(question, evidence)

    if start and end:
        evidence = [
            s for s in evidence
            if s.get("period_start") >= start
            and s.get("period_end") <= end
        ]

    statements = resolve_statements(question, evidence)
    print("DEBUG — resolved statements:", statements)

    # ------------------------------------------------------------
    # 3️⃣ Handle no-evidence case
    # ------------------------------------------------------------
    if not evidence:
        return {
            "answer": "Data is insufficient to answer this question confidently.",
            "evidence_sources": [],
            "confidence": "low",
            "severity": Severity.HIGH.value,
            "limitations": [
                "No relevant financial data was found for the requested time period."
            ],
            "presentation": {
                "main": {"kpis": [], "charts": []},
                "first_degree": {"kpis": [], "charts": []},
                "second_degree": {"kpis": [], "charts": []},
            }
        }

    # ------------------------------------------------------------
    # 4️⃣ Severity + behavior
    # ------------------------------------------------------------
    validation_issues = []
    max_severity = reduce_severity(validation_issues)

    if AGENT_BEHAVIOR[max_severity] == "refuse":
        return {
            "answer": "The available data is insufficient or unreliable to answer this question.",
            "evidence_sources": [],
            "confidence": "low",
            "severity": max_severity.value,
            "limitations": generate_limitations(validation_issues),
            "presentation": {
                "main": {"kpis": [], "charts": []},
                "first_degree": {"kpis": [], "charts": []},
                "second_degree": {"kpis": [], "charts": []},
            }
        }

    # ------------------------------------------------------------
    # 5️⃣ Build answer prompt + run LLM
    # ------------------------------------------------------------
    answer_prompt = build_prompt(question, evidence, statements)
    answer = call_llm(answer_prompt)

    presentation_intent = await call_presentation_llm(
        llm_client=None,
        question=question,
        summaries=evidence,
        statements=statements
    )

    # ------------------------------------------------------------
    # 6️⃣ Build presentation + lineage-aware evidence sources
    # ------------------------------------------------------------
    summary_ids = [s["id"] for s in evidence if s.get("id")]

    conn = get_db_connection()
    try:
        presentation = build_presentation(
            presentation_intent=presentation_intent,
            summaries=evidence,
            db_conn=conn
        )

        summary_ids = list({
            e["summary_id"]
            for e in evidence
            if e.get("summary_id")
        })

        evidence_sources = retrieve_evidence_sources_from_summaries(
            conn=conn,
            summary_ids=summary_ids
        )

        print(evidence_sources)
    finally:
        conn.close()

    # ------------------------------------------------------------
    # 7️⃣ Confidence + limitations
    # ------------------------------------------------------------
    confidence = compute_confidence(
        max_severity=max_severity,
        estimated_ratio=0.0,
        source_confidence=0.8,
    )

    limitations = generate_limitations(validation_issues)
    if any(
        chart.get("is_proxy")
        for section in presentation.values()
        for chart in section["charts"]
    ):
        limitations.append(
            "Some charts use proxy metrics due to unavailable direct metrics."
        )

    # ------------------------------------------------------------
    # 8️⃣ Final response
    # ------------------------------------------------------------
    print(evidence_sources)
    return {
        "answer": answer,
        "evidence_sources": evidence_sources,
        "confidence": confidence,
        "severity": max_severity.value,
        "limitations": limitations,
        "presentation": presentation
    }
