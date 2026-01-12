# app/response/final_response_agent.py

from app.llm.local_llm import call_llm

SYSTEM_PROMPT = """
You are an AI CFO.

Rules:
- You MUST use only the facts and evidence provided.
- Do NOT invent numbers or explanations.
- Always cite evidence explicitly.
- If data is insufficient, say so clearly.
- Be concise, executive-level, and financially precise.
"""

def build_prompt(payload: dict) -> str:
    facts = payload.get("facts", {})
    evidence = payload.get("evidence", [])
    limitations = payload.get("limitations", [])

    prompt = f"""
CEO Question:
{payload['question']}

Verified Financial Facts:
"""
    for k, v in facts.items():
        prompt += f"- {k}: {v}\n"

    prompt += "\nSupporting Evidence:\n"
    for i, e in enumerate(evidence, start=1):
        prompt += f"[Evidence {i}] {e['summary']}\n"

    if limitations:
        prompt += "\nKnown Limitations:\n"
        for l in limitations:
            prompt += f"- {l}\n"

    prompt += """
Respond as a CFO.
Structure your answer clearly.
Cite evidence like (Evidence 1).
"""

    return prompt


def generate_final_answer(payload: dict) -> str:
    prompt = build_prompt(payload)
    return call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=prompt
    )
