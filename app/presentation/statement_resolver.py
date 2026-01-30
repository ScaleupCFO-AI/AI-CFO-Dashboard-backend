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

    # --------------------------------------------------
    # 1️⃣ Evidence-driven signal (highest priority)
    # --------------------------------------------------
    for s in summaries:
        st = s.get("statement_type")
        if st in scores:
            scores[st] += 2

    # --------------------------------------------------
    # 2️⃣ Question keyword signal (CSV-aligned, conservative)
    # --------------------------------------------------
    q = question.lower()

    # --- P&L metrics ---
    pnl_keywords = [
        "revenue",
        "cogs",
        "gross profit",
        "gross margin",
        "operating expense",
        "operating income",
        "ebitda",
        "net profit",
        "net income",
        "margin",
        "profit",
    ]

    # --- Cash Flow metrics ---
    cash_flow_keywords = [
        "cash",
        "cash balance",
        "ending cash",
        "burn",
        "burn rate",
        "runway",
        "runway months",
        "cash runway",
        "operating cash flow",
        "investing cash flow",
        "financing cash flow",
        "net change cash",
    ]

    # --- Balance Sheet metrics ---
    balance_sheet_keywords = [
        "asset",
        "assets",
        "liability",
        "liabilities",
        "equity",
        "debt",
        "total debt",
        "total assets",
        "inventory",
        "accounts receivable",
        "accounts payable",
        "working capital",
    ]

    if any(k in q for k in pnl_keywords):
        scores["pnl"] += 3

    if any(k in q for k in cash_flow_keywords):
        scores["cash_flow"] += 3

    if any(k in q for k in balance_sheet_keywords):
        scores["balance_sheet"] += 3

    # --------------------------------------------------
    # 3️⃣ Keep only statements with signal, ordered by strength
    # --------------------------------------------------
    ordered = [
        s for s, score in sorted(scores.items(), key=lambda x: -x[1])
        if score > 0
    ]

    return ordered
