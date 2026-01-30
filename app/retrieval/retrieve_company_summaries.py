import psycopg2
import os
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


def retrieve_company_summaries(company_id: str, limit: int = 12):
    """
    Deterministic retrieval for dashboard baseline.
    No LLM. No embeddings. No question.
    """

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        SELECT
            s.content,
            p.period_start,
            p.period_end,
            p.period_type,
            p.fiscal_year,
            p.fiscal_quarter,
            s.summary_type
        FROM financial_summaries s
        LEFT JOIN financial_periods p
          ON s.period_id = p.id
        WHERE s.company_id = %s
        ORDER BY p.period_start ASC NULLS LAST
    
        LIMIT %s;
        """,
        (company_id, limit),
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return rows
