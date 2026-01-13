import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


def store_validation_issues(company_id, issues):
    """
    Stores validation + normalization issues.

    - period_date is optional
    - normalization issues → period_date = NULL
    """

    if not issues:
        return

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    for issue in issues:
        cur.execute(
            """
            insert into financial_validations (
                company_id,
                period_date,
                rule,
                severity,
                message
            )
            values (%s, %s, %s, %s, %s)
            """,
            (
                company_id,
                issue.get("period_date"),   # may be None
                issue.get("issue_type"),
                issue.get("severity"),
                issue.get("reason"),
            )
        )

    conn.commit()
    cur.close()
    conn.close()
