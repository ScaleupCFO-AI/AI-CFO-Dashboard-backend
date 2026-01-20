from fastapi import APIRouter
from psycopg2.extras import RealDictCursor
import psycopg2
from dotenv import load_dotenv
import os
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

router = APIRouter()

@router.get("/company/{company_id}/overview")
def get_company_overview(company_id: str):
    """
    Company-level KPIs.
    Deterministic.
    No LLM.
    """

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        select
            sum(case when md.metric_key = 'revenue' then ff.value else 0 end) as total_revenue,
            sum(case when md.metric_key = 'cogs' then ff.value else 0 end) as total_cogs,
            sum(case when md.metric_key = 'ebitda' then ff.value else 0 end) as total_ebitda
        from financial_facts ff
        join metric_definitions md on md.id = ff.metric_id
        where ff.company_id = %s;
        """,
        (company_id,),
    )

    row = cur.fetchone()
    cur.close()
    conn.close()

    return {
        "total_revenue": row["total_revenue"],
        "total_expenses": row["total_cogs"],
        "net_profit": row["total_ebitda"],
    }
