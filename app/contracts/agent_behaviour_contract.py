from app.contracts.severity import Severity

AGENT_BEHAVIOR = {
    Severity.CRITICAL: "refuse",
    Severity.HIGH: "warn",
    Severity.MEDIUM: "caveat",
    Severity.LOW: "normal",
    Severity.INFO: "normal",
}
