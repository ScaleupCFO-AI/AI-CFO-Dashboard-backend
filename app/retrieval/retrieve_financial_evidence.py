import psycopg2
import os
from dotenv import load_dotenv

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
    query_embedding = [0.0] * 1536
    embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute(
        """
        select
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
        order by e.embedding <-> %s
        limit %s;
        """,
        (company_id, embedding_str, top_k)
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    evidence = []
    for (
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
