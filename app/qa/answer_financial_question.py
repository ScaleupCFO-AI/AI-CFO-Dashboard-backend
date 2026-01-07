# from app.retrieval.retrieve_financial_evidence import retrieve_financial_evidence
# from app.qa.claude_prompt import build_prompt
# from anthropic import Anthropic
# import os

# client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# def answer_question(question):
#     evidence = retrieve_financial_evidence(question)

#     if not evidence:
#         return "Insufficient data to answer this question."

#     prompt = build_prompt(question, evidence)

#     response = client.messages.create(
#         model="claude-3-5-sonnet-20240620",
#         max_tokens=500,
#         temperature=0.2,
#         messages=[{"role": "user", "content": prompt}]
#     )

#     return response.content[0].text


# if __name__ == "__main__":
#     q = input("Ask a CFO question: ")
#     print(answer_question(q))

from app.retrieval.retrieve_financial_evidence import retrieve_financial_evidence
from app.qa.claude_prompt import build_prompt
from app.llm.local_llm import call_llm


def answer_question(question):
    evidence = retrieve_financial_evidence(question)

    if not evidence:
        return "Insufficient data to answer this question."

    prompt = build_prompt(question, evidence)

    answer = call_llm(prompt)
    return answer


if __name__ == "__main__":
    q = input("Ask a CFO question: ")
    print(answer_question(q))
