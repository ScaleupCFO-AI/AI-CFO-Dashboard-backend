import os
import psycopg2
from datetime import datetime, timezone
from dotenv import load_dotenv
import calendar
import logging

logger = logging.getLogger("summaries")

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


def generate_and_store_monthly_summary(company_id: str):
    """
    Deterministic monthly summaries from SQL facts.
    - SQL is the source of truth
    - No calculations
    - Idempotent
    """

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # ------------------------------------------------------------
    # 1. Fetch monthly facts
    # ------------------------------------------------------------
    cur.execute(
        """
        select
            p.id,
            p.period_start,
            p.period_end,
            p.fiscal_year,
            m.display_name,
            f.value
        from financial_facts f
        join financial_periods p on f.period_id = p.id
        join metric_definitions m on f.metric_id = m.id
        where p.company_id = %s
          and p.period_type = 'month'
        order by p.period_start asc;
        """,
        (company_id,),
    )

    rows = cur.fetchall()
    if not rows:
        cur.close()
        conn.close()
        return

    # ------------------------------------------------------------
    # 2. Group by period
    # ------------------------------------------------------------
    periods = {}

    for (
        period_id,
        start,
        end,
        fiscal_year,
        metric_name,
        value,
    ) in rows:

        if period_id not in periods:
            periods[period_id] = {
                "start": start,
                "end": end,
                "fiscal_year": fiscal_year,
                "metrics": [],
            }

        periods[period_id]["metrics"].append((metric_name, value))

    # ------------------------------------------------------------
    # 3. Generate summaries (deterministic text)
    # ------------------------------------------------------------
    for period_id, data in sorted(
        periods.items(), key=lambda x: x[1]["start"]
    ):
        month_name = calendar.month_name[data["start"].month]
        year = data["start"].year

        lines = [
            f"Financial summary for {month_name} {year} "
            f"({data['start']} to {data['end']})."
        ]

        for name, value in data["metrics"]:
            lines.append(f"- {name}: {value}")

        summary_text = "\n".join(lines)

        logger.info(
            "Financial summary generated",
            extra={
                "company_id": str(company_id),
                "summary_type": "monthly",
                "period_start": str(data["start"]),
                "period_end": str(data["end"]),
            },
        )

        # --------------------------------------------------------
        # 4. Upsert summary
        # --------------------------------------------------------
        cur.execute(
            """
            insert into financial_summaries (
                company_id,
                period_id,
                summary_type,
                content,
                created_at
            )
            values (%s, %s, 'monthly', %s, %s)
            on conflict (company_id, period_id, summary_type)
            do update set
                content = excluded.content,
                created_at = excluded.created_at;
            """,
            (
                company_id,
                period_id,
                summary_text,
                datetime.now(timezone.utc),
            ),
        )

    conn.commit()
    cur.close()
    conn.close()
