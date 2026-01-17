from app.retrieval.retrieve_financial_evidence import retrieve_financial_evidence
from app.qa.claude_prompt import build_prompt
from app.llm.local_llm import call_llm

from app.contracts.ingestion_quality_contract import reduce_severity
from app.contracts.agent_behaviour_contract import AGENT_BEHAVIOR
from app.contracts.confidence_contract import compute_confidence
from app.contracts.limitations_contract import generate_limitations
from app.contracts.severity import Severity


def answer_question(question: str, company_id: str) -> dict:
    """
    Contract-compliant financial question answering.

    Principles:
    - SQL + summaries are the source of truth
    - LLM is used ONLY for reasoning and explanation
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
        }

    # ------------------------------------------------------------
    # 3️⃣ Collect validation issues from evidence (if present)
    # ------------------------------------------------------------
    # NOTE:
    # Today, retrieve_financial_evidence does not yet attach issues.
    # So we defensively assume no issues.
    # This will improve once agents are introduced.
    validation_issues = []

    # ------------------------------------------------------------
    # 4️⃣ Reduce severity deterministically
    # ------------------------------------------------------------
    max_severity = reduce_severity(validation_issues)

    # ------------------------------------------------------------
    # 5️⃣ Decide agent behavior (refuse / warn / caveat / normal)
    # ------------------------------------------------------------
    behavior = AGENT_BEHAVIOR[max_severity]

    if behavior == "refuse":
        return {
            "answer": "The available data is insufficient or unreliable to answer this question.",
            "evidence": evidence,
            "confidence": "low",
            "severity": max_severity.value,
            "limitations": generate_limitations(validation_issues),
        }

    # ------------------------------------------------------------
    # 6️⃣ Build prompt strictly from evidence
    # ------------------------------------------------------------
    prompt = build_prompt(question, evidence)

    # ------------------------------------------------------------
    # 7️⃣ Call LLM (reasoning only)
    # ------------------------------------------------------------
    answer = call_llm(prompt)

    # ------------------------------------------------------------
    # 8️⃣ Compute confidence deterministically
    # ------------------------------------------------------------
    # Simple, safe defaults for now
    # (will be upgraded once source confidence & estimation ratios are wired)
    confidence = compute_confidence(
        max_severity=max_severity,
        estimated_ratio=0.0,      # placeholder until estimation tracking exists
        source_confidence=0.8,    # placeholder average confidence
    )

    # ------------------------------------------------------------
    # 9️⃣ Generate limitations (machine-derived)
    # ------------------------------------------------------------
    limitations = generate_limitations(validation_issues)

    return {
        "answer": answer,
        "evidence": evidence,
        "confidence": confidence,
        "severity": max_severity.value,
        "limitations": limitations,
    }


if __name__ == "__main__":
    q = input("Ask a CFO question: ")
    company_id = input("Enter company ID: ")
    response = answer_question(q, company_id)

    print("\nANSWER:")
    print(response["answer"])

    print("\nCONFIDENCE:", response["confidence"])
    print("SEVERITY:", response["severity"])

    if response["limitations"]:
        print("\nLIMITATIONS:")
        for l in response["limitations"]:
            print("-", l)
