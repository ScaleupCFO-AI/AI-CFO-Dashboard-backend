import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# 🔑 Map semantic severities to DB-allowed severities
SEVERITY_MAP = {
    "info": "low",
    "warning": "medium",
    "error": "high",
    "critical": "high",
}


def store_validation_issues(company_id, issues):
    """
    Store validation issues in validation_issues table.

    - Resolves metric_id and period_id if possible
    - Maps semantic severities (info, warning, etc.)
      to canonical DB severities (low, medium, high)
    """

    if not issues:
        return

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    for issue in issues:

        metric_id = None
        period_id = None

        metric_key = issue.get("metric_key")
        period_start = issue.get("period_start")

        # Resolve metric_id if metric already exists
        if metric_key:
            cur.execute(
                "select id from metric_definitions where metric_key = %s;",
                (metric_key,)
            )
            row = cur.fetchone()
            if row:
                metric_id = row[0]

        # Resolve period_id if period already exists
        if period_start:
            cur.execute(
                """
                select id from financial_periods
                where company_id = %s
                  and period_start = %s;
                """,
                (company_id, period_start)
            )
            row = cur.fetchone()
            if row:
                period_id = row[0]

        severity = SEVERITY_MAP.get(issue.get("severity", "low"), "low")

        cur.execute(
            """
            insert into validation_issues (
                company_id,
                period_id,
                metric_id,
                issue_type,
                severity,
                description
            )
            values (%s, %s, %s, %s, %s, %s);
            """,
            (
                company_id,
                period_id,
                metric_id,
                issue.get("issue_type"),
                severity,
                issue.get("description") or issue.get("reason"),
            )
        )

    conn.commit()
    cur.close()
    conn.close()
