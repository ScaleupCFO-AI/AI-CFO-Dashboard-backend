import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def store_validation_issues(company_id, issues):
    if not issues:
        return

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    for issue in issues:
        cur.execute(
            """
            insert into financial_validations
            (company_id, period_date, rule, severity, message)
            values (%s, %s, %s, %s, %s)
            """,
            (
                company_id,
                issue["period_date"],
                issue["rule"],
                issue["severity"],
                issue["message"]
            )
        )

    conn.commit()
    cur.close()
    conn.close()
