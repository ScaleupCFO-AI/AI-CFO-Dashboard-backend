# app/contracts/agent_output.py

def empty_agent_output(agent_name: str) -> dict:
    """
    Returns a standard empty response for any agent.
    This prevents shape mismatches across agents.
    """
    return {
        "agent": agent_name,
        "facts": {},
        "analysis": "",
        "evidence": [],
        "limitations": []
    }

# Allowed evidence source types
ALLOWED_EVIDENCE_SOURCES = {
    "table",     # postgres tables
    "summary",   # generated summaries
    "csv",       # uploaded files
    "gl",        # general ledger
    "bank"       # bank statements
}
