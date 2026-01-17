from typing import Set, List, Dict, Optional
from app.normalization.schema_definitions import (
    EXPECTED_METRICS_GLOBAL,
    EXPECTED_METRICS_BY_INDUSTRY,
)


def check_missing_expected_metrics(
    statement_type: str,
    present_metrics: Set[str],
    industry: Optional[str] = None,
) -> List[Dict]:
    """
    Detects missing expected metrics.
    Expectations are SOFT:
    - Used only for validation issues & confidence scoring
    - Never block ingestion
    """

    issues = []

    # 1. Start with global expectations
    expected = set(EXPECTED_METRICS_GLOBAL.get(statement_type, set()))

    # 2. Add industry-specific expectations (if any)
    if industry:
        industry_expectations = EXPECTED_METRICS_BY_INDUSTRY.get(industry, {})
        expected |= set(industry_expectations.get(statement_type, set()))

    if not expected:
        return issues

    missing = expected - present_metrics

    for metric in missing:
        issues.append(
            {
                "issue_type": "missing_expected_metric",
                "severity": "high",
                "metric_name": metric,
                "statement_type": statement_type,
                "industry": industry,
                "description": (
                    f"Expected metric '{metric}' is missing "
                    f"for statement '{statement_type}'"
                    + (f" (industry={industry})" if industry else "")
                ),
            }
        )

    return issues
