def validate_monthly_financials(df):
    issues = []

    if df["Revenue"].isnull().any():
        issues.append({
            "table": "financial_periods",
            "period": "unknown",
            "severity": "critical",
            "issue_type": "missing_revenue",
            "description": "Revenue missing for one or more periods"
        })

    if df["COGS"].isnull().any():
        issues.append({
            "table": "financial_periods",
            "period": "unknown",
            "severity": "high",
            "issue_type": "missing_cogs",
            "description": "COGS missing; margin unreliable"
        })

    return issues
