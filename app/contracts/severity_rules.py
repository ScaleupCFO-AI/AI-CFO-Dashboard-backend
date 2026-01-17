from app.contracts.severity import Severity

SEVERITY_RULES = [
    {
        "metric_key": "revenue",
        "condition": "missing_latest",
        "severity": Severity.CRITICAL,
        "reason": "Revenue missing for latest period",
    },
    {
        "metric_key": "cogs",
        "condition": "missing_latest",
        "severity": Severity.HIGH,
        "reason": "COGS missing; margin analysis unreliable",
    },
    {
        "metric_key": "cash_balance",
        "condition": "missing_latest",
        "severity": Severity.MEDIUM,
        "reason": "Cash balance missing for latest period",
    },
]
