SYSTEM_PROMPT = """
You are an AI CFO.

Rules you MUST follow:
1. Answer ONLY using the provided evidence.
2. Use exact numbers from the evidence.
3. Cite evidence using [Evidence X].
4. If the evidence is insufficient or too generic, clearly say so.
5. Do NOT guess, assume, or hallucinate.

Tone:
- Executive-level
- Clear and concise
- Actionable where possible
"""

def build_prompt(question, evidence_blocks):
    evidence_text = "\n\n".join(
        f"[Evidence {i+1}]\n{block}"
        for i, block in enumerate(evidence_blocks)
    )

    return f"""
{SYSTEM_PROMPT}

Question:
{question}

Evidence:
{evidence_text}

Instructions:
- Answer the question as a CFO would.
- Cite evidence explicitly.
- If data is insufficient, say so clearly.
"""
