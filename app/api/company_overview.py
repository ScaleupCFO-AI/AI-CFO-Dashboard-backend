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
    Deterministic company overview.

    RULES:
    - Uses ONLY stored financial_facts
    - No recomputation of derived metrics
    - Aggregation strictly follows metric semantics
    """

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # --------------------------------------------------
    # Total Revenue (SUM)
    # --------------------------------------------------
    cur.execute(
        """
        SELECT SUM(ff.value) AS total_revenue
        FROM financial_facts ff
        JOIN metric_definitions md ON md.id = ff.metric_id
        WHERE ff.company_id = %s
          AND md.metric_key = 'revenue';
        """,
        (company_id,),
    )
    total_revenue = cur.fetchone()["total_revenue"]

    # --------------------------------------------------
    # Net Profit (SUM — nullable)
    # --------------------------------------------------
    cur.execute(
        """
        SELECT SUM(ff.value) AS net_profit
        FROM financial_facts ff
        JOIN metric_definitions md ON md.id = ff.metric_id
        WHERE ff.company_id = %s
          AND md.metric_key = 'net_profit';
        """,
        (company_id,),
    )
    net_profit = cur.fetchone()["net_profit"]

    # --------------------------------------------------
    # AOV (AVG – derived metric)
    # --------------------------------------------------
    cur.execute(
        """
        SELECT AVG(ff.value) AS aov
        FROM financial_facts ff
        JOIN metric_definitions md ON md.id = ff.metric_id
        WHERE ff.company_id = %s
          AND md.metric_key = 'aov';
        """,
        (company_id,),
    )
    aov = cur.fetchone()["aov"]

    # --------------------------------------------------
    # Repeat Order Rate (AVG – derived metric)
    # --------------------------------------------------
    cur.execute(
        """
        SELECT AVG(ff.value) AS repeat_order_pct
        FROM financial_facts ff
        JOIN metric_definitions md ON md.id = ff.metric_id
        WHERE ff.company_id = %s
          AND md.metric_key = 'repeat_order_rate';
        """,
        (company_id,),
    )
    repeat_order_pct = cur.fetchone()["repeat_order_pct"]

    # --------------------------------------------------
    # Cash Runway (LAST by period_end)
    # --------------------------------------------------
    cur.execute(
        """
        SELECT ff.value
        FROM financial_facts ff
        JOIN metric_definitions md ON md.id = ff.metric_id
        JOIN financial_periods fp ON fp.id = ff.period_id
        WHERE ff.company_id = %s
          AND md.metric_key = 'runway_months'
        ORDER BY fp.period_end DESC
        LIMIT 1;
        """,
        (company_id,),
    )
    runway_row = cur.fetchone()
    cash_runway_months = runway_row["value"] if runway_row else None

    cur.close()
    conn.close()

    return {
        "total_revenue": total_revenue,
        "net_profit": net_profit,
        "aov": aov,
        "repeat_order_pct": repeat_order_pct,
        "cash_runway_months": cash_runway_months,
    }
