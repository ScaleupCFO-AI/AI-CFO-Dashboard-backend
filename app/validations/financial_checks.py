def validate_monthly_financials(df):
    """
    Validation MUST run on canonical schema only.
    Canonical columns are lowercase.
    """

    issues = []

    # Revenue column missing entirely
    if "revenue" not in df.columns:
        issues.append({
            "issue_type": "missing_revenue_column",
            "severity": "critical",
            "reason": "Revenue column missing after normalization",
            "period_date": None,
        })
        return issues  # cannot validate further

    # Revenue values missing
    if df["revenue"].isnull().any():
        issues.append({
            "issue_type": "missing_revenue_values",
            "severity": "critical",
            "reason": "Revenue missing for one or more periods",
            "period_date": None,
        })

    # COGS missing (optional but important)
    if "cogs" in df.columns and df["cogs"].isnull().any():
        issues.append({
            "issue_type": "missing_cogs_values",
            "severity": "high",
            "reason": "COGS missing; margin unreliable",
            "period_date": None,
        })

    return issues
