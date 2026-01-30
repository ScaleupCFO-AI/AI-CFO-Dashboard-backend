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

from app.presentation.presentation_llm import call_presentation_llm
from app.presentation.presentation_builder import build_presentation
from app.presentation.statement_resolver import resolve_statements
from app.presentation.chart_intents import ChartIntent
from app.presentation.deterministic_metric_hints import extract_metric_hints
from app.metrics.metric_registry import get_all_metric_keys
from app.presentation.baseline_presentation import (
    get_company_baseline as fetch_company_baseline
)

from app.qa.helpers import (
    dedupe_with_priority,
    rebalance_sections,
    section_empty,
)

from app.db.connection import get_db_connection
from app.ingestion.period_derivation import resolve_time_range


async def answer_question(question: str, company_id: str) -> dict:
    print("\n================ ANSWER QUESTION =================")
    print("QUESTION:", question)

    # ------------------------------------------------------------
    # 1️⃣ Retrieve evidence summaries (ROUTING + CONTEXT ONLY)
    # ------------------------------------------------------------
    evidence = retrieve_financial_evidence(question, company_id)
    evidence = sorted(evidence, key=lambda x: x.get("period_start") or "")
    print(f"[DEBUG] Retrieved {len(evidence)} evidence summaries")

    # ------------------------------------------------------------
    # 2️⃣ Resolve time range from summaries
    # ------------------------------------------------------------
    start, end = resolve_time_range(question, evidence)
    print(f"[DEBUG] Resolved time range: {start} → {end}")

    if start and end:
        evidence = [
            s for s in evidence
            if s.get("period_start") >= start
            and s.get("period_end") <= end
        ]
        print(f"[DEBUG] Evidence after time filter: {len(evidence)}")

    # ------------------------------------------------------------
    # 3️⃣ Resolve statements + deterministic KPI hints
    # ------------------------------------------------------------
    statements = resolve_statements(question, evidence)
    print("[DEBUG] Resolved statements:", statements)

    all_metric_keys = get_all_metric_keys()
    deterministic_root_kpis = extract_metric_hints(
        question,
        all_metric_keys
    )
    print("[DEBUG] Deterministic root KPI hints:", deterministic_root_kpis)

    # ------------------------------------------------------------
    # 4️⃣ No evidence → HARD baseline fallback
    # ------------------------------------------------------------
    if not evidence:
        baseline = fetch_company_baseline(company_id)
        return {
            "answer": "Data is insufficient to answer this question confidently.",
            "evidence_sources": [],
            "confidence": "low",
            "severity": Severity.HIGH.value,
            "limitations": ["No relevant financial data found."],
            "presentation": baseline,
        }

    # ------------------------------------------------------------
    # 5️⃣ Severity gate (data quality)
    # ------------------------------------------------------------
    max_severity = reduce_severity([])

    if AGENT_BEHAVIOR[max_severity] == "refuse":
        baseline = fetch_company_baseline(company_id)
        return {
            "answer": "Data is insufficient or unreliable.",
            "evidence_sources": [],
            "confidence": "low",
            "severity": max_severity.value,
            "limitations": generate_limitations([]),
            "presentation": baseline,
        }

    # ------------------------------------------------------------
    # 6️⃣ Presentation intent (LLM-safe, no facts)
    # ------------------------------------------------------------
    presentation_intent = await call_presentation_llm(
        llm_client=None,
        question=question,
        summaries=evidence,          # routing only
        statements=statements,
        seed_root_kpis=deterministic_root_kpis
    )

    if presentation_intent.intent is None:
        presentation_intent.intent = ChartIntent.TREND

    print("[DEBUG] Presentation intent:", presentation_intent)

    # ------------------------------------------------------------
    # 7️⃣ Build presentation (SOURCE OF TRUTH = SQL FACTS)
    # ------------------------------------------------------------
    conn = get_db_connection()
    try:
        presentation = build_presentation(
            presentation_intent=presentation_intent,
            summaries=evidence,   # still passed, not used
            db_conn=conn,
            company_id=company_id,
        )


        presentation = dedupe_with_priority(presentation)

        baseline = fetch_company_baseline(company_id)
        presentation = rebalance_sections(
            presentation=presentation,
            baseline=baseline
        )

        presentation = dedupe_with_priority(presentation)

        if section_empty(presentation["main"]):
            presentation = baseline

        # Evidence lineage (audit / UI)
        summary_ids = list({
            e["summary_id"]
            for e in evidence
            if e.get("summary_id")
        })

        evidence_sources = retrieve_evidence_sources_from_summaries(
            conn=conn,
            summary_ids=summary_ids
        )

    finally:
        conn.close()

    print("[DEBUG] FINAL PRESENTATION:", presentation)

    # ------------------------------------------------------------
    # 7.5️⃣ Extract KPI CONTEXT summaries (QUALITATIVE ONLY)
    # Convention: summary_type = <grain>_<purpose>
    # Context summaries end with "_context"
    # ------------------------------------------------------------
    kpi_context = [
        e["content"]
        for e in evidence
        if e.get("summary_type", "").endswith("_context")
    ]

    print("[DEBUG] KPI CONTEXT COUNT:", len(kpi_context))

    # ------------------------------------------------------------
    # 8️⃣ LLM ANSWER (FACTS + CONTEXT, CLEARLY SEPARATED)
    # ------------------------------------------------------------
    answer = call_llm(
        build_prompt(
            question=question,
            presentation=presentation,   # authoritative facts
            context=kpi_context          # qualitative framing only
        )
    )

    # ------------------------------------------------------------
    # 9️⃣ Confidence + limitations (NOT summaries)
    # ------------------------------------------------------------
    confidence = compute_confidence(
        max_severity=max_severity,
        estimated_ratio=0.0,
        source_confidence=0.8,
    )

    limitations = generate_limitations([])

    print("================================================\n")

    return {
        "answer": answer,
        "evidence_sources": evidence_sources,
        "confidence": confidence,
        "severity": max_severity.value,
        "limitations": limitations,
        "presentation": presentation,
    }
