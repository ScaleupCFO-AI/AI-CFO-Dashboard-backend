import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


def fetch_recent_facts(company_id: str, limit: int = 50):
    """
    Read-only helper.
    Returns the canonical facts actually inserted into SQL.
    """

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute(
        """
        select
            p.period_type,
            p.period_start,
            p.period_end,
            m.metric_key,
            m.display_name,
            f.value,
            f.source_system
        from financial_facts f
        join financial_periods p on f.period_id = p.id
        join metric_definitions m on f.metric_id = m.id
        where f.company_id = %s
        order by f.created_at desc
        limit %s;
        """,
        (company_id, limit),
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    facts = []
    for (
        period_type,
        period_start,
        period_end,
        metric_key,
        display_name,
        value,
        source_system,
    ) in rows:
        facts.append({
            "period_type": period_type,
            "period_start": period_start,
            "period_end": period_end,
            "metric_key": metric_key,
            "metric_name": display_name,
            "value": value,
            "source": source_system,
        })

    return facts
