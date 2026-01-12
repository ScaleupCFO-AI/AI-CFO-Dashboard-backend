# app/contracts/ingestion_contract.py
from app.contracts.severity import Severity
SOURCE_CONFIDENCE = {
    "zoho_api": 0.95,
    "tally_api": 0.90,
    "bank_api": 0.98,

    "csv_upload": 0.70,
    "xlsx_upload": 0.65,

    "sec_derived": 0.50,
    "pdf_extracted": 0.45,

    "user_estimated": 0.30,
}
SEVERITY_SEMANTICS = {
    "critical": {
        "meaning": "Data unusable",
        "agent_behavior": "refuse_answer"
    },
    "high": {
        "meaning": "Likely misleading",
        "agent_behavior": "answer_with_strong_warning"
    },
    "medium": {
        "meaning": "Incomplete but usable",
        "agent_behavior": "answer_with_caveats"
    },
    "low": {
        "meaning": "Minor issue",
        "agent_behavior": "answer_normally"
    },
    "info": {
        "meaning": "Informational",
        "agent_behavior": "ignore"
    }
}
REQUIRED_FINANCIAL_FIELDS = {
    "financial_periods": [
        "company_id",
        "period_date",

        # core financial facts (nullable allowed)
        "revenue",
        "cogs",
        "gross_profit",
        "ebitda",
        "cash_closing",
        "runway_months"
    ]
}
SEVERITY_RULES = [
    {
        "condition": "latest_period.revenue is NULL",
        "severity": Severity.CRITICAL.value,
        "reason": "Cannot reason about performance without revenue"
    },
    {
        "condition": "latest_period.cogs is NULL",
        "severity": Severity.HIGH.value,
        "reason": "Margin analysis becomes unreliable"
    },
    {
        "condition": "ebitda derived from aggregated data",
        "severity": Severity.MEDIUM.value,
        "reason": "Precision loss due to aggregation"
    },
    {
        "condition": "historical_period_missing",
        "severity": Severity.LOW.value,
        "reason": "Does not affect current decisions"
    },
    {
        "condition": "column_name_mapped",
        "severity": Severity.INFO.value,
        "reason": "Cosmetic ingestion issue"
    }
]
