import os
import psycopg2
from datetime import datetime, timezone
from dotenv import load_dotenv
import calendar
from collections import defaultdict

from app.summarization.context_registry import MONTHLY_CONTEXT_REGISTRY

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

def generate_monthly_context_summaries(company_id: str):
    """
    Orchestrates monthly KPI context summaries.

    Responsibilities:
    - Fetch SQL facts
    - Group by metric + period
    - Call KPI context generators
    - Persist summaries + lineage
    """

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # ------------------------------------------------------------
    # 1. Fetch all monthly facts for context-eligible KPIs
    # ------------------------------------------------------------
    metric_keys = list(MONTHLY_CONTEXT_REGISTRY.keys())

    cur.execute(
        """
        SELECT
            p.id AS period_id,
            p.period_start,
            m.metric_key,
            f.value
        FROM financial_facts f
        JOIN financial_periods p ON f.period_id = p.id
        JOIN metric_definitions m ON f.metric_id = m.id
        WHERE p.company_id = %s
          AND p.period_type = 'month'
          AND m.metric_key = ANY(%s)
        ORDER BY m.metric_key, p.period_start ASC;
        """,
        (company_id, metric_keys),
    )

    rows = cur.fetchall()
    if not rows:
        cur.close()
        conn.close()
        return

    # ------------------------------------------------------------
    # 2. Organize by metric → ordered values per period
    # ------------------------------------------------------------
    by_metric = defaultdict(list)

    for period_id, period_start, metric_key, value in rows:
        by_metric[metric_key].append(
            {
                "period_id": period_id,
                "period_start": period_start,
                "value": value,
            }
        )

    # ------------------------------------------------------------
    # 3. Generate and store summaries
    # ------------------------------------------------------------
    for metric_key, entries in by_metric.items():
        config = MONTHLY_CONTEXT_REGISTRY[metric_key]
        generator = config["generator"]
        summary_type = config["summary_type"]

        values_so_far = []

        for entry in entries:
            values_so_far.append(entry["value"])

            summary_text = generator(values_so_far)

            month_name = calendar.month_name[entry["period_start"].month]
            year = entry["period_start"].year

            full_text = (
                f"{summary_text} "
                f"Period: {month_name} {year}."
            )

            cur.execute(
                """
                INSERT INTO financial_summaries (
                    company_id,
                    period_id,
                    summary_type,
                    content,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (company_id, period_id, summary_type)
                DO UPDATE SET
                    content = EXCLUDED.content,
                    created_at = EXCLUDED.created_at
                RETURNING id;
                """,
                (
                    company_id,
                    entry["period_id"],
                    summary_type,
                    full_text,
                    datetime.now(timezone.utc),
                ),
            )

            summary_id = cur.fetchone()[0]
            _insert_summary_sources(
                cur,
                company_id,
                entry["period_id"],
                summary_id,
            )

    conn.commit()
    cur.close()
    conn.close()
