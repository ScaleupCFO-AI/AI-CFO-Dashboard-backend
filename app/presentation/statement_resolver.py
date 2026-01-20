def resolve_statements(question: str, summaries: list) -> list[str]:
    """
    Returns ordered list of relevant financial statements.
    First = primary, rest = supporting.
    """

    scores = {
        "pnl": 0,
        "cash_flow": 0,
        "balance_sheet": 0,
    }

    # 1️⃣ Evidence-driven signal (highest priority)
    for s in summaries:
        st = s.get("statement_type")
        if st in scores:
            scores[st] += 2

    # 2️⃣ Question keyword signal (conservative)
    q = question.lower()

    if any(k in q for k in ["revenue", "margin", "expense", "profit", "cogs"]):
        scores["pnl"] += 3

    if any(k in q for k in ["cash", "burn", "runway"]):
        scores["cash_flow"] += 3

    if any(k in q for k in ["asset", "liability", "equity", "balance"]):
        scores["balance_sheet"] += 3

    # Keep only statements with signal, ordered by strength
    ordered = [
        s for s, score in sorted(scores.items(), key=lambda x: -x[1])
        if score > 0
    ]

    return ordered
 
