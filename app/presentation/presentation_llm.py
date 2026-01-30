import json
from app.presentation.presentation_schema import PresentationIntent, IntentEnum
from app.presentation.available_metrics import extract_available_metrics
from app.presentation.kpi_registry import STATEMENT_KPIS
from app.llm.local_llm import call_llm


def sanitize_intent(value: str | None) -> IntentEnum | None:
    if not value:
        return None
    try:
        return IntentEnum(value.strip())
    except Exception:
        return None


PRESENTATION_SYSTEM_PROMPT = """
You are an AI CFO presentation planner.

YOUR JOB:
Select which KPIs should be visualized and assign EXACTLY ONE chart intent per KPI.

━━━━━━━━━━ STRICT RULES (NON-NEGOTIABLE) ━━━━━━━━━━
1. You may ONLY choose KPIs from the Allowed KPIs list.
2. You MUST use metric_key EXACTLY as provided.
3. You MUST NOT invent new KPIs.
4. You MUST assign ONE intent per KPI — NOT multiple.
5. You MUST diversify intents across KPIs for better UX.

━━━━━━━━━━ INTENT OPTIONS ━━━━━━━━━━
- trend
- snapshot
- comparison
- contribution
- variance

━━━━━━━━━━ DIVERSITY GUIDELINES ━━━━━━━━━━

- Do NOT assign the same intent to all KPIs.
- Even if all KPIs are time-varying, you MUST diversify intents.

DEFAULT BEHAVIOR:
- Select at most ONE primary KPI for "trend"
- For other time-series KPIs, prefer:
  - comparison → bar chart (period comparison)
  - snapshot → KPI tile (latest value only)

PREFERENCES:
- snapshot → balance metrics (cash_balance, runway)
- contribution → mix metrics (channel_mix, geo_mix, product_mix)
- trend → ONE key performance driver only
- comparison → profit, margin, or cost metrics

Use snapshot sparingly, but USE IT when needed for diversity.

━━━━━━━━━━ CHART TYPE RULES (CRITICAL) ━━━━━━━━━━

Each KPI MUST map to exactly ONE chart type via its intent.

Use these mappings:

- trend → line chart
- snapshot → KPI card (single value)
- comparison → bar chart
- contribution → stacked bar or pie chart
- variance → bar chart (positive vs negative)

IMPORTANT DIVERSITY CONSTRAINTS:
- If more than 1 KPI is selected:
  - DO NOT assign "trend" to all KPIs
  - At least ONE KPI must use:
    - snapshot OR
    - comparison OR
    - contribution
- Even if metrics are time-series, you may still use:
  - snapshot (latest period)
  - comparison (across periods)
  - contribution (if logically meaningful)

If unsure:
- Pick ONE KPI as trend
- Pick ONE KPI as snapshot or comparison


━━━━━━━━━━ YOU MUST NOT ━━━━━━━━━━
- Decide KPI hierarchy
- Compute or derive metrics
- Explain anything
- Output text outside JSON

━━━━━━━━━━ OUTPUT FORMAT (STRICT JSON ONLY) ━━━━━━━━━━

{
  "root_kpis": ["metric_key"],
  "intent": "trend | snapshot | comparison | contribution | variance",
  "kpi_intents": {
    "metric_key": "trend | snapshot | comparison | contribution | variance"
  },
  "time_scope": null
}

━━━━━━━━━━ CRITICAL CONSTRAINTS ━━━━━━━━━━
- "intent" MUST be exactly ONE value
- Each KPI must have exactly ONE intent
- NEVER use "|", lists, or combined values
- Extra keys are FORBIDDEN
- If unsure, choose the single BEST intent

━━━━━━━━━━ ✅ CORRECT EXAMPLES ━━━━━━━━━━

Question: How is revenue?
Output:
{
  "root_kpis": ["revenue"],
  "intent": "trend",
  "kpi_intents": {
    "revenue": "trend"
  },
  "time_scope": null
}

Question: Give a CEO-level overview of our financial situation
Output:
{
  "root_kpis": ["revenue", "cogs", "operating_expense", "net_profit", "cash_balance"],
  "intent": "snapshot",
  "kpi_intents": {
    "revenue": "trend",
    "cogs": "trend",
    "operating_expense": "trend",
    "net_profit": "comparison",
    "cash_balance": "snapshot"
  },
  "time_scope": null
}

━━━━━━━━━━ ❌ INCORRECT (DO NOT DO THIS) ━━━━━━━━━━

❌ "intent": "trend | snapshot"
❌ "kpi_intents": { "revenue": "trend | contribution" }
❌ Multiple intents for one KPI
❌ KPIs not in Allowed KPIs

━━━━━━━━━━ FINAL INSTRUCTION ━━━━━━━━━━
Return ONLY valid JSON.
NO markdown.
NO explanations.
NO extra text.
"""



def build_presentation_prompt(question, summaries, allowed_kpis):
    summaries_text = "\n".join(
        f"- {s['content']}" for s in summaries if s.get("content")
    )

    return f"""
{PRESENTATION_SYSTEM_PROMPT}

Allowed KPIs (metric_key ONLY):
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
    statements: list[str],
    seed_root_kpis: list[str]
) -> PresentationIntent:

    available_metrics = sorted(extract_available_metrics(summaries))

    if statements:
        primary = statements[0]
        allowed_kpis = sorted({
            m for m in STATEMENT_KPIS.get(primary, [])
            if m in available_metrics
        })
    else:
        allowed_kpis = []

    print("[DEBUG] Allowed KPIs for presentation LLM:", allowed_kpis)

    prompt = build_presentation_prompt(
        question=question,
        summaries=summaries,
        allowed_kpis=allowed_kpis
    )

    raw = call_llm(prompt)
    print("[DEBUG] Presentation LLM raw output:\n", raw)

    try:
        parsed = json.loads(raw)

        parsed["intent"] = sanitize_intent(parsed.get("intent"))

        parsed["kpi_intents"] = {
            k: sanitize_intent(v).value
            for k, v in parsed.get("kpi_intents", {}).items()
            if sanitize_intent(v)
        }

        intent = PresentationIntent.model_validate(parsed)

    except Exception as e:
        print("[ERROR] Presentation LLM parse failed:", e)
        intent = PresentationIntent(
            root_kpis=[],
            intent=None,
            kpi_intents={},
            time_scope=None
        )

    # 🔐 HARD GUARANTEES
    intent.root_kpis = list(set(seed_root_kpis + intent.root_kpis))

    if intent.intent is None:
        intent.intent = IntentEnum.trend

    cleaned_kpi_intents = {}
    for kpi in intent.root_kpis:
        cleaned_kpi_intents[kpi] = (
            intent.kpi_intents.get(kpi, intent.intent)
        )

    intent.kpi_intents = cleaned_kpi_intents

    print("[DEBUG] Final root KPIs:", intent.root_kpis)
    print("[DEBUG] Final KPI intents:", intent.kpi_intents)

    return intent
