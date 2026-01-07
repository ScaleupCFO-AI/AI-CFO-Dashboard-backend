import psycopg2
import os
from dotenv import load_dotenv

from app.summarization.monthly_summary import generate_monthly_summary
from app.summarization.store_summary import store_summary

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# 🔁 Replace with your company_id
COMPANY_ID = "09b31214-8785-464f-928a-8d2c939db3b8"



def fetch_financials():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute(
        """
        select
            period_date,
            revenue,
            cogs,
            gross_profit,
            ebitda,
            cash_closing,
            runway_months
        from financial_periods
        where company_id = %s
        order by period_date asc
        """,
        (COMPANY_ID,)
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            "period_date": r[0],
            "revenue": float(r[1]),
            "cogs": float(r[2]),
            "gross_profit": float(r[3]),
            "ebitda": float(r[4]),
            "cash_closing": float(r[5]),
            "runway_months": float(r[6]),
        }
        for r in rows
    ]


def fetch_validations():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute(
        """
        select
            period_date,
            rule,
            severity,
            message
        from financial_validations
        where company_id = %s
        """,
        (COMPANY_ID,)
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            "period_date": r[0],
            "rule": r[1],
            "severity": r[2],
            "message": r[3],
        }
        for r in rows
    ]


def main():
    financials = fetch_financials()
    validations = fetch_validations()

    summary_text = generate_monthly_summary(financials, validations)

    if not summary_text:
        print("No summary generated.")
        return

    store_summary(
        company_id=COMPANY_ID,
        summary_text=summary_text,
        start_date=financials[0]["period_date"],
        end_date=financials[-1]["period_date"],
    )

    print("Financial summary generated and stored.")


if __name__ == "__main__":
    main()
