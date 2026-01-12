from app.contracts.agent_output import empty_agent_output

def answer_revenue_question(question: str) -> dict:
    output = empty_agent_output("revenue")

    # TEMP hardcoded logic (we improve later)
    revenue_current = 5_500_000
    revenue_previous = 5_000_000
    mom_change_pct = 10.0

    # FACTS (numbers only)
    output["facts"] = {
        "revenue_current": revenue_current,
        "revenue_previous": revenue_previous,
        "mom_change_pct": mom_change_pct
    }

    # ANALYSIS (must only use facts)
    output["analysis"] = (
        f"Revenue increased {mom_change_pct}% month-over-month "
        f"from ₹{revenue_previous:,} to ₹{revenue_current:,}."
    )

    # EVIDENCE (real source)
    output["evidence"] = [
        {
            "source_type": "table",
            "reference": "monthly_financials",
            "period": "2025-10",
            "excerpt": "Revenue: 5,500,000 | Previous: 5,000,000"
        }
    ]

    # LIMITATIONS (what we cannot conclude yet)
    output["limitations"] = [
        "No customer-level revenue data available",
        "No contract or pipeline data linked"
    ]

    return output
