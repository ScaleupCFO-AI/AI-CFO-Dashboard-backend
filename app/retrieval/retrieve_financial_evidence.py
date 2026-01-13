# app/retrieval/retrieve_financial_evidence.py

import os
import psycopg2
from dotenv import load_dotenv

from app.embeddings.generate_embedding import generate_embedding

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


def retrieve_financial_evidence(
    question: str,
    company_id: str,
    top_k: int = 5
):
    """
    Returns top_k most relevant financial summaries for a given company and question.
    Evidence is ALWAYS SQL-backed. No hardcoded data.
    """

    # 1️⃣ Generate embedding for the question
    query_embedding = generate_embedding(question)
    embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

    # 2️⃣ Query pgvector-backed summaries
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            summary_text,
            summary_type,
            period_start,
            period_end,
            embedding <-> %s::vector AS distance
        FROM financial_summaries
        WHERE company_id = %s
        ORDER BY distance
        LIMIT %s;
        """,
        (embedding_str, company_id, top_k)
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    # 3️⃣ Structure evidence (NO interpretation)
    evidence = []
    for summary_text, summary_type, start, end, distance in rows:
        evidence.append({
            "summary": summary_text,
            "type": summary_type,
            "period_start": start,
            "period_end": end,
            "distance": float(distance)
        })

    return evidence
