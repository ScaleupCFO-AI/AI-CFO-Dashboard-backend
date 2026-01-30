import os
from datetime import datetime, timezone
from collections import defaultdict

import pandas as pd
import psycopg2
from dotenv import load_dotenv

from app.ingestion.ingest_company import ensure_company_exists
from app.ingestion.ingestion_helpers import (
    compute_file_hash,
    get_or_create_source_document,
    get_or_create_period,
    normalize_metric_key,
)
from app.ingestion.period_derivation import (
    derive_fiscal_year_from_date,
    derive_period_dates,
    extract_calendar_month,
)
from app.normalization.column_mapper import normalize_columns
from app.normalization.schema_definitions import CANONICAL_FIELDS
from app.validations.metric_completeness import check_missing_expected_metrics
from app.validations.store_issues import store_validation_issues
from app.summarization.monthly_summary import generate_monthly_context_summaries
from app.generate_financial_summaries import (
    generate_and_store_quarterly_uploaded_summary,
    generate_and_store_yearly_uploaded_summary,
)
from app.embeddings.generate_embedding import embed_missing_summaries

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


def ingest_financial_file(
    file_path: str,
    user_email: str,
    company_name: str | None = None,
    source_type: str = "csv",
    source_grain: str = "monthly",
    is_estimated: bool = False,
    original_filename: str | None = None,  # ✅ ADD
):

    """
    Canonical, deterministic ingestion pipeline.

    GUARANTEES:
    - period_date is the single source of truth for time
    - only metrics in metric_definitions are ingested
    - no LLM required for date parsing
    """

    # ------------------------------------------------------------
    # 0. Resolve company
    # ------------------------------------------------------------
    company_id = ensure_company_exists(
        company_email=user_email,
        company_name=company_name,
    )

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # ------------------------------------------------------------
    # Fetch fiscal year start month + industry
    # ------------------------------------------------------------
    cur.execute(
        """
        SELECT fiscal_year_start_month, industry_code
        FROM companies
        WHERE id = %s;
        """,
        (company_id,),
    )
    fiscal_year_start_month, industry_code = cur.fetchone()

    # ------------------------------------------------------------
    # Fetch canonical metrics registry
    # ------------------------------------------------------------
    cur.execute(
        """
        SELECT
            metric_key,
            statement_type_id,
            aggregation_type,
            is_derived,
            allowed_grains
        FROM metric_definitions;
        """
    )

    canonical_metrics = [
        {
            "metric_key": row[0],
            "statement_type_id": row[1],
            "aggregation_type": row[2],
            "is_derived": row[3],
            "allowed_grains": row[4],
        }
        for row in cur.fetchall()
    ]

    # ------------------------------------------------------------
    # 1. Register source document
    # ------------------------------------------------------------
    file_hash = compute_file_hash(file_path)

    source_doc = get_or_create_source_document(
        cur=cur,
        company_id=company_id,
        file_hash=file_hash,
        source_type=source_type,
        source_name=original_filename or os.path.basename(file_path),
    )

    source_document_id = source_doc["id"]

    if source_doc["status"] == "completed":
        cur.close()
        conn.close()
        return {"company_id": company_id, "message": "Already ingested"}

    # ------------------------------------------------------------
    # 2. Parse file
    # ------------------------------------------------------------
    if file_path.lower().endswith((".csv", ".txt")):
        raw_df = pd.read_csv(file_path)
    elif file_path.lower().endswith((".xlsx", ".xls")):
        raw_df = pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file type")

    # ------------------------------------------------------------
    # 3. Normalize columns
    # ------------------------------------------------------------
    canonical_df, report = normalize_columns(
        raw_df,
        CANONICAL_FIELDS,
        source_metadata={
            "source": source_type,
            "source_grain": source_grain,
            "is_estimated": is_estimated,
        },
        canonical_metrics=canonical_metrics,
    )

    store_validation_issues(company_id, report.get("issues", []))

    if "period_date" not in canonical_df.columns:
        raise ValueError("period_date is required for ingestion")

    # ------------------------------------------------------------
    # 4. Metric completeness validation
    # ------------------------------------------------------------
    present_metrics = {
        normalize_metric_key(col)
        for col in canonical_df.columns
        if col != "period_date"
    }

    cur.execute(
        """
        SELECT md.metric_key, st.name
        FROM metric_definitions md
        JOIN statement_types st ON md.statement_type_id = st.id
        WHERE md.metric_key = ANY(%s);
        """,
        (list(present_metrics),),
    )

    metric_to_statement = dict(cur.fetchall())
    present_metrics_by_statement = defaultdict(set)

    for metric_key, statement_name in metric_to_statement.items():
        present_metrics_by_statement[statement_name.lower()].add(metric_key)

    for statement_name, metrics in present_metrics_by_statement.items():
        issues = check_missing_expected_metrics(
            statement_type=statement_name,
            present_metrics=metrics,
            industry=industry_code,
        )
        store_validation_issues(company_id, issues)

    # ------------------------------------------------------------
    # 5. Determine period type
    # ------------------------------------------------------------
    if source_grain not in {"monthly", "quarter", "year"}:
        raise ValueError(f"Unsupported source_grain: {source_grain}")

    period_type = (
        "month" if source_grain == "monthly"
        else "quarter" if source_grain == "quarter"
        else "year"
    )

    # ------------------------------------------------------------
    # 6. Insert financial facts (WITH source_document_id ✅)
    # ------------------------------------------------------------
    for _, row in canonical_df.iterrows():

        period_date = row["period_date"]

        fiscal_year = derive_fiscal_year_from_date(
            value=period_date,
            fiscal_year_start_month=fiscal_year_start_month,
        )

        if period_type == "month":
            fiscal_month = extract_calendar_month(period_date)
            fiscal_quarter = None
        elif period_type == "quarter":
            raise ValueError("Quarterly uploads must include quarter info")
        else:
            fiscal_month = None
            fiscal_quarter = None

        period_start, period_end = derive_period_dates(
            period_type=period_type,
            fiscal_year=fiscal_year,
            fiscal_quarter=fiscal_quarter,
            fiscal_month=fiscal_month,
            fiscal_year_start_month=fiscal_year_start_month,
        )

        period_id = get_or_create_period(
            cur=cur,
            company_id=company_id,
            period_start=period_start,
            period_end=period_end,
            period_type=period_type,
            fiscal_year=fiscal_year,
            fiscal_quarter=fiscal_quarter,
            fiscal_month=fiscal_month,
        )

        for col, value in row.items():
            if col == "period_date" or value is None:
                continue

            metric_key = normalize_metric_key(col)

            cur.execute(
                "SELECT id FROM metric_definitions WHERE metric_key = %s;",
                (metric_key,),
            )
            res = cur.fetchone()
            if not res:
                continue

            cur.execute(
                """
                INSERT INTO financial_facts (
                    company_id,
                    period_id,
                    metric_id,
                    value,
                    source_system,
                    source_document_id
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
                """,
                (
                    company_id,
                    period_id,
                    res[0],
                    value,
                    source_type,
                    source_document_id,
                ),
            )

    conn.commit()

    # ------------------------------------------------------------
    # 7. Generate summaries + embeddings
    # ------------------------------------------------------------
    generate_monthly_context_summaries(company_id)
    generate_and_store_quarterly_uploaded_summary(company_id)
    generate_and_store_yearly_uploaded_summary(company_id)
    embed_missing_summaries(company_id)

    cur.execute(
        """
        UPDATE source_documents
        SET ingestion_status = 'completed',
            last_processed_at = %s
        WHERE id = %s;
        """,
        (datetime.now(timezone.utc), source_document_id),
    )
    conn.commit()

    cur.close()
    conn.close()

    return {"company_id": company_id, "message": "Ingestion completed"}
