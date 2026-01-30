import psycopg2
import os
from dotenv import load_dotenv
from app.embeddings.generate_embedding import generate_embedding

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


def retrieve_financial_evidence(
    question: str,
    company_id: str,
    top_k: int = 5,
):
    """
    Retrieve top-K relevant financial summaries using vector similarity.

    Schema-aligned:
    - financial_summaries.content
    - joins financial_periods for time context
    """

    # Placeholder embedding until real model is wired
    if not question or not question.strip():
        raise ValueError("Question text cannot be empty")

    # ------------------------------------------------------------
    # 1. Generate query embedding (REAL, NOT STUB)
    # ------------------------------------------------------------
    query_embedding = generate_embedding(question)

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute(
        """
        select
    s.id as summary_id,
    s.content,
    p.period_start,
    p.period_end,
    p.period_type,
    p.fiscal_year,
    p.fiscal_quarter,
    s.summary_type
from financial_summaries s
join summary_embeddings e
  on s.id = e.summary_id
left join financial_periods p
  on s.period_id = p.id
where s.company_id = %s
ORDER BY e.embedding <-> %s::vector
limit %s;

        """,
        (company_id, query_embedding, top_k)
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    evidence = []
    for (
    summary_id,
    content,
    period_start,
    period_end,
    period_type,
    fiscal_year,
    fiscal_quarter,
    summary_type,
) in rows:

        evidence.append(
    {
        "summary_id": summary_id,   # 🔑 REQUIRED
        "content": content,
        "period_start": period_start,
        "period_end": period_end,
        "period_type": period_type,
        "fiscal_year": fiscal_year,
        "fiscal_quarter": fiscal_quarter,
        "summary_type": summary_type,
    }
)


    return evidence
