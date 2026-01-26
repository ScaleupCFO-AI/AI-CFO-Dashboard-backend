import os
import psycopg2
from datetime import datetime, timezone
from dotenv import load_dotenv
import calendar
import logging

logger = logging.getLogger("summaries")

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


def _insert_summary_sources(cur, company_id, period_id, summary_id):
    """
    Insert deterministic lineage between summary and source_documents.
    """

    cur.execute(
        """
        SELECT DISTINCT source_document_id
        FROM financial_facts
        WHERE company_id = %s
          AND period_id = %s;
        """,
        (company_id, period_id),
    )

    source_rows = cur.fetchall()

    for (source_document_id,) in source_rows:
        cur.execute(
            """
            INSERT INTO summary_sources (
                summary_id,
                source_document_id
            )
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING;
            """,
            (summary_id, source_document_id),
        )


def generate_and_store_monthly_summary(company_id: str):
    """
    Deterministic monthly summaries from SQL facts.
    """

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            p.id,
            p.period_start,
            p.period_end,
            p.fiscal_year,
            m.display_name,
            f.value
        FROM financial_facts f
        JOIN financial_periods p ON f.period_id = p.id
        JOIN metric_definitions m ON f.metric_id = m.id
        WHERE p.company_id = %s
          AND p.period_type = 'month'
        ORDER BY p.period_start ASC;
        """,
        (company_id,),
    )

    rows = cur.fetchall()
    if not rows:
        cur.close()
        conn.close()
        return

    periods = {}

    for period_id, start, end, fiscal_year, metric_name, value in rows:
        if period_id not in periods:
            periods[period_id] = {
                "start": start,
                "end": end,
                "fiscal_year": fiscal_year,
                "metrics": [],
            }
        periods[period_id]["metrics"].append((metric_name, value))

    for period_id, data in sorted(periods.items(), key=lambda x: x[1]["start"]):
        month_name = calendar.month_name[data["start"].month]
        year = data["start"].year

        lines = [
            f"Financial summary for {month_name} {year} "
            f"({data['start']} to {data['end']})."
        ]

        for name, value in data["metrics"]:
            lines.append(f"- {name}: {value}")

        summary_text = "\n".join(lines)

        cur.execute(
            """
            INSERT INTO financial_summaries (
                company_id,
                period_id,
                summary_type,
                content,
                created_at
            )
            VALUES (%s, %s, 'monthly', %s, %s)
            ON CONFLICT (company_id, period_id, summary_type)
            DO UPDATE SET
                content = EXCLUDED.content,
                created_at = EXCLUDED.created_at
            RETURNING id;
            """,
            (
                company_id,
                period_id,
                summary_text,
                datetime.now(timezone.utc),
            ),
        )

        summary_id = cur.fetchone()[0]
        _insert_summary_sources(cur, company_id, period_id, summary_id)

    conn.commit()
    cur.close()
    conn.close()


def generate_and_store_quarterly_uploaded_summary(company_id: str):
    """
    Deterministic summaries for uploaded quarterly data only.
    """

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            p.id,
            p.period_start,
            p.period_end,
            p.fiscal_year,
            p.fiscal_quarter,
            m.display_name,
            f.value
        FROM financial_facts f
        JOIN financial_periods p ON f.period_id = p.id
        JOIN metric_definitions m ON f.metric_id = m.id
        WHERE p.company_id = %s
          AND p.period_type = 'quarter'
        ORDER BY p.period_start ASC;
        """,
        (company_id,),
    )

    rows = cur.fetchall()
    if not rows:
        cur.close()
        conn.close()
        return

    periods = {}

    for (
        period_id,
        start,
        end,
        fiscal_year,
        fiscal_quarter,
        metric_name,
        value,
    ) in rows:

        if period_id not in periods:
            periods[period_id] = {
                "start": start,
                "end": end,
                "fiscal_year": fiscal_year,
                "quarter": fiscal_quarter,
                "metrics": [],
            }

        periods[period_id]["metrics"].append((metric_name, value))

    for period_id, data in periods.items():
        header = (
            f"Financial summary based on uploaded quarterly data "
            f"for Q{data['quarter']} FY{data['fiscal_year']}"
        )

        if data["start"] and data["end"]:
            header += f" ({data['start']} to {data['end']})."
        else:
            header += "."

        lines = [header]

        for name, value in data["metrics"]:
            lines.append(f"- {name}: {value}")

        summary_text = "\n".join(lines)

        cur.execute(
            """
            INSERT INTO financial_summaries (
                company_id,
                period_id,
                summary_type,
                content,
                created_at
            )
            VALUES (%s, %s, 'quarterly_uploaded', %s, %s)
            ON CONFLICT (company_id, period_id, summary_type)
            DO UPDATE SET
                content = EXCLUDED.content,
                created_at = EXCLUDED.created_at
            RETURNING id;
            """,
            (
                company_id,
                period_id,
                summary_text,
                datetime.now(timezone.utc),
            ),
        )

        summary_id = cur.fetchone()[0]
        _insert_summary_sources(cur, company_id, period_id, summary_id)

    conn.commit()
    cur.close()
    conn.close()


def generate_and_store_yearly_uploaded_summary(company_id: str):
    """
    Deterministic summaries for uploaded yearly data only.
    """

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            p.id,
            p.period_start,
            p.period_end,
            p.fiscal_year,
            m.display_name,
            f.value
        FROM financial_facts f
        JOIN financial_periods p ON f.period_id = p.id
        JOIN metric_definitions m ON f.metric_id = m.id
        WHERE p.company_id = %s
          AND p.period_type = 'year'
        ORDER BY p.period_start ASC;
        """,
        (company_id,),
    )

    rows = cur.fetchall()
    if not rows:
        cur.close()
        conn.close()
        return

    periods = {}

    for period_id, start, end, fiscal_year, metric_name, value in rows:
        if period_id not in periods:
            periods[period_id] = {
                "start": start,
                "end": end,
                "fiscal_year": fiscal_year,
                "metrics": [],
            }

        periods[period_id]["metrics"].append((metric_name, value))

    for period_id, data in periods.items():
        header = f"Financial summary based on uploaded yearly data for FY{data['fiscal_year']}"

        if data["start"] and data["end"]:
            header += f" ({data['start']} to {data['end']})."
        else:
            header += "."

        lines = [header]

        for name, value in data["metrics"]:
            lines.append(f"- {name}: {value}")

        summary_text = "\n".join(lines)

        cur.execute(
            """
            INSERT INTO financial_summaries (
                company_id,
                period_id,
                summary_type,
                content,
                created_at
            )
            VALUES (%s, %s, 'yearly_uploaded', %s, %s)
            ON CONFLICT (company_id, period_id, summary_type)
            DO UPDATE SET
                content = EXCLUDED.content,
                created_at = EXCLUDED.created_at
            RETURNING id;
            """,
            (
                company_id,
                period_id,
                summary_text,
                datetime.now(timezone.utc),
            ),
        )

        summary_id = cur.fetchone()[0]
        _insert_summary_sources(cur, company_id, period_id, summary_id)

    conn.commit()
    cur.close()
    conn.close()
