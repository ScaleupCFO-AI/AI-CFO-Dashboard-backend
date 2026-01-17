# app/contracts/confidence_contract.py

from app.contracts.severity import Severity

def compute_confidence(
    max_severity: Severity,
    estimated_ratio: float,
    source_confidence: float,
) -> str:
    """
    Deterministic confidence computation.
    """

    if max_severity == Severity.CRITICAL:
        return "low"

    if max_severity == Severity.HIGH:
        return "medium"

    if estimated_ratio > 0.3:
        return "medium"

    if source_confidence < 0.7:
        return "medium"

    return "high"
