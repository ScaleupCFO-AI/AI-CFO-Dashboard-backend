import json
from app.presentation.presentation_schema import PresentationIntent
from app.presentation.kpi_registry import STATEMENT_KPIS
from app.llm.local_llm import call_llm


PRESENTATION_SYSTEM_PROMPT = """
You are an AI CFO presentation planner.

YOUR JOB:
Identify ALL KPIs the user is directly asking about.

IMPORTANT:
- You do NOT decide supporting KPIs
- You do NOT decide hierarchy
- You do NOT explain anything

OUTPUT RULES (NON-NEGOTIABLE):
- Output MUST be valid JSON
- Output MUST match the EXACT schema below
- Output MUST NOT contain any text outside JSON

ALLOWED INTENTS:
- trend
- snapshot
- comparison
- contribution
- variance

FORBIDDEN:
- Analysis
- Explanations
- KPIs not in the allowed list

EXACT OUTPUT SCHEMA:

{
  "root_kpis": ["string"],
  "intent": "trend|snapshot|comparison|contribution|variance",
  "time_scope": null
}
"""


def build_presentation_prompt(question, summaries, statements):
    primary = statements[0] if statements else None
    allowed_kpis = sorted(STATEMENT_KPIS.get(primary, []))

    summaries_text = "\n".join(
        f"- {s['content']}"
        for s in summaries
        if s.get("content")
    )

    return f"""
{PRESENTATION_SYSTEM_PROMPT}

Allowed KPIs:
{allowed_kpis}

Question:
{question}

Financial summaries:
{summaries_text}

Return ONLY valid JSON.
"""


async def call_presentation_llm(
    llm_client,
    question: str,
    summaries: list,
    statements: list[str]
) -> PresentationIntent:

    prompt = build_presentation_prompt(question, summaries, statements)
    raw = call_llm(prompt)

    try:
        parsed = json.loads(raw)
        return PresentationIntent.model_validate(parsed)
    except Exception:
        return PresentationIntent(
            root_kpis=[],
            intent=None,
            time_scope=None
        )
