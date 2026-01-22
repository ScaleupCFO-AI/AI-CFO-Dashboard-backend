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
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            SUM(CASE WHEN md.metric_key = 'revenue' THEN ff.value ELSE 0 END) AS total_revenue,
            SUM(CASE WHEN md.metric_key = 'net_profit' THEN ff.value ELSE 0 END) AS net_profit,
            AVG(CASE WHEN md.metric_key = 'aov' THEN ff.value END) AS aov,
            AVG(CASE WHEN md.metric_key = 'repeat_order_rate' THEN ff.value END) AS repeat_order_pct,
            MAX(CASE WHEN md.metric_key = 'cash_balance' THEN ff.value END) AS cash_balance,
            AVG(CASE WHEN md.metric_key = 'burn_rate' THEN ff.value END) AS burn_rate
        FROM financial_facts ff
        JOIN metric_definitions md ON md.id = ff.metric_id
        WHERE ff.company_id = %s;
    """, (company_id,))

    row = cur.fetchone()
    cur.close()
    conn.close()

    cash_runway_months = None
    if row["cash_balance"] and row["burn_rate"] and row["burn_rate"] > 0:
        cash_runway_months = int(row["cash_balance"] / row["burn_rate"])

    return {
        "total_revenue": row["total_revenue"] or 0,
        "net_profit": row["net_profit"] or 0,
        "aov": row["aov"],
        "repeat_order_pct": row["repeat_order_pct"],
        "cash_runway_months": cash_runway_months,
    }
