import asyncio

from app.retrieval.retrieve_financial_evidence import retrieve_financial_evidence
from app.qa.claude_prompt import build_prompt
from app.llm.local_llm import call_llm

from app.contracts.ingestion_quality_contract import reduce_severity
from app.contracts.agent_behaviour_contract import AGENT_BEHAVIOR
from app.contracts.confidence_contract import compute_confidence
from app.contracts.limitations_contract import generate_limitations
from app.contracts.severity import Severity

# 🔽 NEW IMPORTS (presentation layer)
from app.presentation.presentation_llm import call_presentation_llm
from app.presentation.presentation_builder import build_presentation
from app.presentation.statement_resolver import resolve_statements



async def answer_question(question: str, company_id: str) -> dict:
    """
    Contract-compliant financial question answering.

    Principles:
    - SQL + summaries are the source of truth
    - LLM is used ONLY for reasoning and explanation
    - Presentation logic is SEPARATE and deterministic
    - Confidence, severity, limitations are deterministic
    - No hallucinated numbers
    """

    # ------------------------------------------------------------
    # 1️⃣ Retrieve evidence (SQL + pgvector summaries)
    # ------------------------------------------------------------
    evidence = retrieve_financial_evidence(
        question=question,
        company_id=company_id
    )

    # Sort evidence chronologically (important for trend questions)
    evidence = sorted(
        evidence,
        key=lambda x: x.get("period_start") or ""
    )
    statements = resolve_statements(question, evidence)

    print("DEBUG — resolved statements:", statements)


    # ------------------------------------------------------------
    # 2️⃣ Handle no-evidence case (hard stop)
    # ------------------------------------------------------------
    if not evidence:
        return {
            "answer": "Data is insufficient to answer this question confidently.",
            "evidence": [],
            "confidence": "low",
            "severity": Severity.HIGH.value,
            "limitations": [
                "No relevant financial summaries were found for the uploaded data."
            ],
            "presentation": {
                "main": {"kpis": [], "charts": []},
                "first_degree": {"kpis": [], "charts": []},
                "second_degree": {"kpis": [], "charts": []},
            }
        }

    # ------------------------------------------------------------
    # 3️⃣ Collect validation issues (future-ready)
    # ------------------------------------------------------------
    validation_issues = []

    # ------------------------------------------------------------
    # 4️⃣ Reduce severity deterministically
    # ------------------------------------------------------------
    max_severity = reduce_severity(validation_issues)

    # ------------------------------------------------------------
    # 5️⃣ Decide agent behavior
    # ------------------------------------------------------------
    behavior = AGENT_BEHAVIOR[max_severity]

    if behavior == "refuse":
        return {
            "answer": "The available data is insufficient or unreliable to answer this question.",
            "evidence": evidence,
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
    # 6️⃣ Build answer prompt strictly from evidence
    # ------------------------------------------------------------
    answer_prompt = build_prompt(question, evidence, statements)

    # ------------------------------------------------------------
    # 7️⃣ Run LLM calls IN PARALLEL
    # ------------------------------------------------------------
    answer =call_llm(answer_prompt)
    

    presentation_intent = await call_presentation_llm(
    llm_client=None,
    question=question,
    summaries=evidence,
    statements=statements
    )

    presentation = build_presentation(
        presentation_intent=presentation_intent,
        summaries=evidence
    )


    # ------------------------------------------------------------
    # 9️⃣ Compute confidence deterministically
    # ------------------------------------------------------------
    confidence = compute_confidence(
        max_severity=max_severity,
        estimated_ratio=0.0,     # placeholder until estimation tracking exists
        source_confidence=0.8,   # placeholder average confidence
    )

    # ------------------------------------------------------------
    # 🔟 Generate limitations (machine-derived)
    # ------------------------------------------------------------
    limitations = generate_limitations(validation_issues)
    if any(chart.get("is_proxy") for section in presentation.values() for chart in section["charts"]):
        limitations.append(
            "Some charts use proxy metrics due to unavailable direct metrics."
        )

    # ------------------------------------------------------------
    # 1️⃣1️⃣ Final response (ANSWER + CHARTS)
    # ------------------------------------------------------------
    return {
        "answer": answer,
        "evidence": evidence,
        "confidence": confidence,
        "severity": max_severity.value,
        "limitations": limitations,
        "presentation": presentation
    }
