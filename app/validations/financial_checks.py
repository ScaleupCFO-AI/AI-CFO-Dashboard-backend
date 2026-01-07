def validate_monthly_financials(df):
    issues = []

    for _, row in df.iterrows():
        # Rule 1: Revenue must be non-negative
        if row["Revenue"] < 0:
            issues.append({
                "period_date": row["Date"],
                "rule": "negative_revenue",
                "severity": "critical",
                "message": f"Revenue is negative: {row['Revenue']}"
            })

        # Rule 2: Gross profit consistency
        expected_gp = row["Revenue"] - row["COGS"]
        if abs(expected_gp - row["Gross_Profit"]) > 1:
            issues.append({
                "period_date": row["Date"],
                "rule": "gross_profit_mismatch",
                "severity": "warning",
                "message": "Gross profit does not equal Revenue - COGS"
            })

        # Rule 3: Runway sanity check
        if row["Runway_Months"] < 0:
            issues.append({
                "period_date": row["Date"],
                "rule": "negative_runway",
                "severity": "critical",
                "message": "Runway months is negative"
            })

    return issues
