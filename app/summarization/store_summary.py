import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def store_summary(company_id, summary_text, start_date, end_date):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute(
        """
        insert into financial_summaries
        (company_id, period_start, period_end, summary_type, summary_text)
        values (%s, %s, %s, %s, %s)
        """,
        (
            company_id,
            start_date,
            end_date,
            "monthly_overview",
            summary_text
        )
    )

    conn.commit()
    cur.close()
    conn.close()
