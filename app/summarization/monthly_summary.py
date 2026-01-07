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
    critical_issues = [
        v for v in validation_issues if v["severity"] == "critical"
    ]

    if critical_issues:
        summary.append(
            "Critical data quality issues were detected that may affect reliability."
        )

    return " ".join(summary)
