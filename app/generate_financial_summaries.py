import psycopg2
import os
from dotenv import load_dotenv

from app.summarization.monthly_summary import generate_monthly_summary
from app.summarization.store_summary import store_summary

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


def generate_and_store_monthly_summary(company_id: str):
    """
    Generates and stores the monthly financial summary for a company.
    Derived ONLY from canonical SQL facts + validation issues.
    Deterministic and re-runnable.
    """

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # 1️⃣ Fetch canonical financial facts
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
        (company_id,)
    )

    financial_rows = [
        {
            "period_date": r[0],
            "revenue": float(r[1]),
            "cogs": float(r[2]),
            "gross_profit": float(r[3]),
            "ebitda": float(r[4]),
            "cash_closing": float(r[5]),
            "runway_months": float(r[6]),
        }
        for r in cur.fetchall()
    ]

    # 2️⃣ Fetch validation issues
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
        (company_id,)
    )

    validation_rows = [
        {
            "period_date": r[0],
            "rule": r[1],
            "severity": r[2],
            "message": r[3],
        }
        for r in cur.fetchall()
    ]

    cur.close()
    conn.close()

    # 3️⃣ Generate summary text
    summary_text = generate_monthly_summary(
        financial_rows=financial_rows,
        validation_issues=validation_rows
    )

    if not summary_text:
        return None

    # 4️⃣ Store summary
    store_summary(
        company_id=company_id,
        summary_text=summary_text,
        start_date=financial_rows[0]["period_date"],
        end_date=financial_rows[-1]["period_date"],
    )

    return summary_text


# Optional: keep CLI usage for debugging
if __name__ == "__main__":
    cid = input("Enter company ID: ")
    generate_and_store_monthly_summary(cid)
    print("Financial summary generated and stored.")
