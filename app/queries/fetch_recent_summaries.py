import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


def fetch_recent_summaries(company_id: str, limit: int = 10):
    """
    Read-only helper for debugging / preview.
    SQL is the source of truth.
    """

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute(
        """
        select
            s.summary_type,
            p.period_start,
            p.period_end,
            s.content,
            s.created_at
        from financial_summaries s
        left join financial_periods p on s.period_id = p.id
        where s.company_id = %s
        order by s.created_at desc
        limit %s;
        """,
        (company_id, limit),
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    summaries = []
    for summary_type, start, end, content, created_at in rows:
        summaries.append({
            "summary_type": summary_type,
            "period_start": start,
            "period_end": end,
            "content": content,
            "created_at": created_at,
        })

    return summaries
