import json
from app.presentation.presentation_schema import PresentationIntent
from app.presentation.kpi_registry import STATEMENT_KPIS
from app.llm.local_llm import call_llm

PRESENTATION_SYSTEM_PROMPT = """
You are an AI CFO presentation planner.

YOUR JOB:
Decide which charts to show.
You do NOT explain anything.

OUTPUT RULES (NON-NEGOTIABLE):
- Output MUST be valid JSON
- Output MUST match the EXACT schema below
- Output MUST NOT contain any text outside JSON
- Output MUST NOT contain explanations, notes, or comments
- Output MUST NOT contain natural language descriptions
- If no chart is applicable, return empty arrays in the schema

ALLOWED INTENTS:
- trend
- snapshot
- comparison
- contribution
- variance

FORBIDDEN:
- Descriptions (e.g. "increasing", "decreasing")
- Analysis
- Percentages
- Growth rates
- Any keys not listed in the schema

EXACT OUTPUT SCHEMA (copy and fill values only):

{
  "main": [
    {
      "metric": "string",
      "intent": "trend|snapshot|comparison|contribution|variance",
      "time_scope": null
    }
  ],
  "first_degree": [],
  "second_degree": []
}
"""

def build_presentation_prompt(
    question: str,
    summaries: list,
    statements: list[str]
) -> str:

    primary = statements[0] if statements else None
    allowed_kpis = sorted(STATEMENT_KPIS.get(primary, []))

    summaries_text = "\n".join(
        f"- {s['content']}"
        for s in summaries
        if s.get("content")
    )

    print("\n===== PRESENTATION DEBUG =====")
    print("Question:", question)
    print("Resolved statements:", statements)

    primary = statements[0] if statements else None
    print("Primary statement:", primary)

    allowed_kpis = sorted(STATEMENT_KPIS.get(primary, []))
    print("Allowed KPIs:", allowed_kpis)

    return f"""
{PRESENTATION_SYSTEM_PROMPT}

Allowed KPIs for this question:
{allowed_kpis}

Question:
{question}

Financial summaries:
{summaries_text}

Return ONLY valid JSON in this shape:
{{ ... }}
"""

async def call_presentation_llm(
    llm_client,   # kept for future use
    question: str,
    summaries: list,
    statements: list[str]
) -> PresentationIntent:

    prompt = build_presentation_prompt(question, summaries, statements)

    # Use existing synchronous LLM
    raw = call_llm(prompt)
    print("\n----- PRESENTATION LLM RAW OUTPUT -----")
    print(raw)
    print("--------------------------------------")

    try:
        parsed = json.loads(raw)
        print(PresentationIntent.model_validate(parsed))
        return PresentationIntent.model_validate(parsed)
    except Exception:
        return PresentationIntent(main=[], first_degree=[], second_degree=[])
