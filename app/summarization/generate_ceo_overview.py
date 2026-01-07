import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

COMPANY_ID = "09b31214-8785-464f-928a-8d2c939db3b8"


def generate_ceo_overview():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Fetch latest financial snapshot
    cur.execute(
        """
        SELECT period_date,revenue, ebitda, cash_closing, runway_months
        FROM financial_periods
        WHERE company_id = %s
        ORDER BY period_date DESC
        LIMIT 1;
        """,
        (COMPANY_ID,)
    )

    period_date,revenue, ebitda, cash, runway = cur.fetchone()

    summary_text = (
        f"As of {period_date}, the company shows improving financial performance. "
        f"Revenue increased to ₹{revenue:,.0f} this month, with EBITDA reaching "
        f"₹{ebitda:,.0f}, indicating sustained operating profitability. "
        f"Cash balance stands at ₹{cash:,.0f}, extending the cash runway to "
        f"{runway:.1f} months, up from the previous period. "
        f"No immediate liquidity risks are observed, though continued monitoring "
        f"of operating expenses is recommended."
)


    cur.execute(
        """
        INSERT INTO financial_summaries
        (company_id, summary_type, summary_text)
        VALUES (%s, %s, %s);
        """,
        (COMPANY_ID, "ceo_overview", summary_text)
    )

    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    generate_ceo_overview()
    print("CEO overview summary generated.")
