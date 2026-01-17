def validate_monthly_financials(df):
    """
    Validation runs on canonical (normalized) data BEFORE SQL insertion.

    - Does NOT assume fixed schema
    - Emits metric-aware issues
    - Safe for future LLM-based normalization
    """

    issues = []

    for _, row in df.iterrows():

        period_start = row.get("period_start")

        for col, value in row.items():

            # Skip non-metric fields
            if col in {
                "period_start",
                "period_end",
                "period_type",
                "fiscal_year",
                "fiscal_quarter",
            }:
                continue

            metric_key = col.strip().lower().replace(" ", "_")

            # -----------------------------
            # Missing value check
            # -----------------------------
            if value is None:
                issues.append({
                    "issue_type": "missing_value",
                    "severity": "high",
                    "description": f"Missing value for metric '{metric_key}'",
                    "metric_key": metric_key,
                    "period_start": period_start,
                })
                continue

            # -----------------------------
            # Numeric sanity checks
            # -----------------------------
            if isinstance(value, (int, float)):

                if "revenue" in metric_key and value < 0:
                    issues.append({
                        "issue_type": "negative_revenue",
                        "severity": "critical",
                        "description": "Revenue value is negative",
                        "metric_key": metric_key,
                        "period_start": period_start,
                    })

                if "margin" in metric_key and not (-1 <= value <= 1):
                    issues.append({
                        "issue_type": "invalid_margin",
                        "severity": "high",
                        "description": "Margin outside expected range (-1 to 1)",
                        "metric_key": metric_key,
                        "period_start": period_start,
                    })

                if "cash" in metric_key and value < 0:
                    issues.append({
                        "issue_type": "negative_cash",
                        "severity": "medium",
                        "description": "Cash balance is negative",
                        "metric_key": metric_key,
                        "period_start": period_start,
                    })

    return issues
