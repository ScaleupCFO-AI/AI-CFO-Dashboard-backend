# app/contracts/ingestion_quality_contract.py

from app.contracts.severity import Severity

SEVERITY_PRIORITY = [
    Severity.CRITICAL,
    Severity.HIGH,
    Severity.MEDIUM,
    Severity.LOW,
    Severity.INFO,
]

SEVERITY_SCORE = {
    Severity.CRITICAL: 5,
    Severity.HIGH: 4,
    Severity.MEDIUM: 3,
    Severity.LOW: 2,
    Severity.INFO: 1,
}

def reduce_severity(issues: list[dict]) -> Severity:
    """
    Deterministically compute the worst severity.
    """
    if not issues:
        return Severity.INFO

    return max(
        (Severity(issue["severity"]) for issue in issues),
        key=lambda s: SEVERITY_SCORE[s],
    )
