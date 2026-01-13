from collections import Counter
def generate_monthly_summary(financial_rows, validation_issues):
    """
    financial_rows: list of dicts from financial_periods
    validation_issues: list of dicts from financial_validations
    """

    if not financial_rows:
        return None

    latest = financial_rows[-1]
    prev = financial_rows[-2] if len(financial_rows) > 1 else None

    summary = []

    # Revenue trend
    if prev:
        growth = ((latest["revenue"] - prev["revenue"]) / prev["revenue"]) * 100
        summary.append(
            f"Revenue for the latest month was ₹{latest['revenue']:,.0f}, "
            f"representing a {growth:.1f}% month-on-month change."
        )
    else:
        summary.append(
            f"Revenue for the first recorded month was ₹{latest['revenue']:,.0f}."
        )

    # EBITDA
    summary.append(
        f"EBITDA stood at ₹{latest['ebitda']:,.0f}, "
        f"with a closing cash balance of ₹{latest['cash_closing']:,.0f} "
        f"and runway of {latest['runway_months']} months."
    )

    # Validation flags


    issue_counts = Counter(v["severity"] for v in validation_issues)

    if issue_counts:
        notes = []

        if issue_counts.get("critical"):
            notes.append("critical data quality issues")

        if issue_counts.get("high"):
            notes.append("high-severity data ambiguities")

        if issue_counts.get("medium"):
            notes.append("estimated or partially derived data")

        if notes:
            summary.append(
                "Data quality notes: " + ", ".join(notes) +
                ". These may affect the confidence of conclusions."
            )


        return " ".join(summary)
