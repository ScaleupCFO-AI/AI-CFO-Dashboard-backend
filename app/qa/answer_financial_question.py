from app.retrieval.retrieve_financial_evidence import retrieve_financial_evidence
from app.qa.claude_prompt import build_prompt
from app.llm.local_llm import call_llm


def answer_question(question: str, company_id: str) -> dict:
    """
    Contract-compliant question answering using SQL-derived summaries only.

    - NO agents
    - NO generic answers
    - NO hallucinated numbers
    - Evidence-first
    """

    # 1️⃣ Retrieve company-specific, question-specific evidence
    evidence = retrieve_financial_evidence(
        question=question,
        company_id=company_id
    )

    # 2️⃣ Handle insufficient data (deterministic, contract-aligned)
    if not evidence:
        return {
            "answer": "Data is insufficient to answer this question confidently.",
            "evidence": [],
            "confidence": "low",
            "severity": "warning",
            "limitations": [
                "No relevant financial summaries were found for this company based on the uploaded data."
            ]
        }

    # 3️⃣ Build prompt strictly from evidence
    prompt = build_prompt(question, evidence)

    # 4️⃣ Call LLM (LLM reasons, does NOT decide confidence)
    answer = call_llm(prompt)

    # 5️⃣ Determine confidence & severity deterministically
    # (simple, safe rules — agents will improve this later)
    confidence = "high" if len(evidence) >= 3 else "medium"
    severity = "info"

    return {
        "answer": answer,
        "evidence": evidence,
        "confidence": confidence,
        "severity": severity,
        "limitations": []
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
