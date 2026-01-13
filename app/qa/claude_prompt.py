SYSTEM_PROMPT = """
You are an AI CFO.

Rules you MUST follow:
1. Answer ONLY using the provided evidence.
2. Use exact numbers from the evidence.
3. Do NOT reference evidence labels (e.g., do not say "Evidence 1").
4. Do NOT include citations, brackets, or footnotes in your answer.
5. If the evidence is insufficient or too generic, clearly say so.
6. Do NOT guess, assume, or hallucinate.

Tone:
- Executive-level
- Clear and concise
- Factual, not verbose
"""


def build_prompt(question, evidence_blocks):
    evidence_text = "\n\n".join(
        f"- {block['summary']}"
        for block in evidence_blocks
    )

    return f"""
{SYSTEM_PROMPT}

Question:
{question}

Financial Data (use only this information):
{evidence_text}

Instructions:
- Write a clean executive answer.
- Do not mention where the data came from.
- The system will display evidence separately.
"""
