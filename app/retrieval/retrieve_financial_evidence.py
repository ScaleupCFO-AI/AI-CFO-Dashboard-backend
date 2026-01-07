# import os
# import psycopg2
# from dotenv import load_dotenv

# from app.embeddings.generate_embedding import generate_embedding
# from app.dev.local_evidence import LOCAL_EVIDENCE
# USE_LOCAL_EVIDENCE = "true"
# def retrieve_financial_evidence(question):
#     if USE_LOCAL_EVIDENCE:
#         return LOCAL_EVIDENCE

#     # existing Supabase logic below

# load_dotenv()
# DATABASE_URL = os.getenv("DATABASE_URL")

# # same company id you used earlier
# COMPANY_ID = "09b31214-8785-464f-928a-8d2c939db3b8"


# def retrieve_financial_evidence(question: str, top_k: int = 3):
#     """
#     Returns top_k most relevant financial summaries for a question.
#     """
#     query_embedding = generate_embedding(question)
#     embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

#     conn = psycopg2.connect(DATABASE_URL)
#     cur = conn.cursor()

#     cur.execute(
#         """
#         SELECT
#             summary_text,
#             summary_type,
#             period_start,
#             period_end,
#             embedding <-> %s::vector AS distance
#         FROM financial_summaries
#         WHERE company_id = %s
#         ORDER BY distance
#         LIMIT %s;
#         """,
#         (embedding_str, COMPANY_ID, top_k)
#     )

#     results = cur.fetchall()

#     cur.close()
#     conn.close()

#     return results


# if __name__ == "__main__":
#     question = "Give me a CEO-level financial overview"
#     evidence = retrieve_financial_evidence(question)

#     for i, row in enumerate(evidence, start=1):
#         summary, s_type, start, end, dist = row
#         print(f"\nEvidence {i}")
#         print(f"Type: {s_type}")
#         print(f"Period: {start} → {end}")
#         print(f"Distance: {dist:.4f}")
#         print(f"Summary: {summary}")
# app/retrieval/retrieve_financial_evidence.py

USE_LOCAL_EVIDENCE = True

def retrieve_financial_evidence(question: str):
    if USE_LOCAL_EVIDENCE:
        return [
            {
                "type": "ceo_overview",
                "summary": (
                    "As of 2025-10-01, the company shows improving financial performance. "
                    "Monthly revenue stands at ₹5,500,000 with EBITDA of ₹1,530,000. "
                    "Cash balance is ₹7,650,000, providing approximately 15 months of runway. "
                    "No immediate liquidity risks are observed."
                ),
                "period_start": None,
                "period_end": None
            }
        ]

    # ---- DO NOT REACH HERE IN DEV MODE ----
    raise RuntimeError("Supabase retrieval disabled in dev mode")

