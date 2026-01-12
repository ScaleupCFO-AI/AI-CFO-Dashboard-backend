# app/orchestration/response_synthesizer.py

from typing import List, Dict


def synthesize_response(
    query: str,
    agent_responses: List[Dict]
) -> Dict:
    """
    Combines multiple agent outputs into a single CFO-style response.
    """

    if not agent_responses:
        return {
            "answer": (
                "I don’t have sufficient structured data to answer this question yet. "
                "Once financial statements or transactions are available, I can analyze this in detail."
            ),
            "confidence": "low",
            "sources": [],
            "limitations": ["No relevant financial data available"]
        }

    answer_sections = []
    sources = []
    limitations = []

    for response in agent_responses:
        topic = response.get("topic")
        summary = response.get("summary")
        evidence = response.get("evidence", [])
        gaps = response.get("limitations", [])

        if summary:
            answer_sections.append(f"**{topic.upper()}**\n{summary}")

        if evidence:
            sources.extend(evidence)

        if gaps:
            limitations.extend(gaps)

    final_answer = "\n\n".join(answer_sections)

    return {
        "answer": final_answer,
        "confidence": "medium" if len(agent_responses) == 1 else "high",
        "sources": sources,
        "limitations": list(set(limitations))
    }
