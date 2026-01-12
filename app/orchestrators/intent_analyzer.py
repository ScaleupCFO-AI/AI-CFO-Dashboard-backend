# app/orchestration/intent_analyzer.py

from typing import List, Dict

INTENT_KEYWORDS = {
    "revenue": ["revenue", "sales", "income", "growth"],
    "expenses": ["expense", "cost", "spend", "burn"],
    "cash": ["cash", "runway", "liquidity", "survive"],
    "kpis": ["kpi", "target", "metric", "health"]
}


def analyze_intent(query: str) -> List[Dict]:
    """
    Analyze user query and return detected intents with confidence scores.
    Deterministic, rule-based (v1).
    """
    query_lower = query.lower()
    detected_intents = []

    for intent, keywords in INTENT_KEYWORDS.items():
        matches = sum(1 for word in keywords if word in query_lower)

        if matches > 0:
            confidence = min(0.5 + 0.15 * matches, 0.95)
            detected_intents.append({
                "intent": intent,
                "confidence": round(confidence, 2)
            })

    return detected_intents
