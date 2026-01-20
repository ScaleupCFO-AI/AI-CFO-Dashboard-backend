import os
from datetime import datetime, timezone

import pandas as pd
import psycopg2
from dotenv import load_dotenv
from collections import defaultdict
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
    parse_fiscal_year,
    parse_fiscal_quarter,
)
from app.normalization.column_mapper import normalize_columns
from app.normalization.llm_column_mapper import llm_column_mapper
from app.normalization.schema_definitions import CANONICAL_FIELDS
from app.validations.metric_completeness import check_missing_expected_metrics
from app.validations.metric_completeness import check_missing_expected_metrics
from app.validations.store_issues import store_validation_issues
from app.generate_financial_summaries import (generate_and_store_monthly_summary, generate_and_store_quarterly_uploaded_summary, generate_and_store_yearly_uploaded_summary)
from app.embed_financial_summaries import embed_missing_summaries

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


def ingest_financial_file(
    file_path: str,
    user_email: str,
    company_name: str | None = None,
    source_type: str = "csv",
    source_grain: str = "monthly",
    is_estimated: bool = False,
):
    """
    Canonical, resumable ingestion pipeline.
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
    # Fetch fiscal year start month
    # ------------------------------------------------------------
    cur.execute(
    """
    select fiscal_year_start_month, industry_code
    from companies
    where id = %s;
    """,
    (company_id,),
    )
    fiscal_year_start_month, industry_code = cur.fetchone()


    # ------------------------------------------------------------
    # Fetch KPI statement type id ONCE
    # ------------------------------------------------------------
    cur.execute(
        "select id from statement_types where name = 'KPI';"
    )
    kpi_statement_type_id = cur.fetchone()[0]

    # ------------------------------------------------------------
    # 1. Register source document
    # ------------------------------------------------------------
    file_hash = compute_file_hash(file_path)

    source_doc = get_or_create_source_document(
        cur=cur,
        company_id=company_id,
        file_hash=file_hash,
        source_type=source_type,
        source_name=os.path.basename(file_path),
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
    # 3. Extract period identity (RAW)
    # ------------------------------------------------------------
    raw_df["_period_month"] = raw_df.get("Month")
    raw_df["_period_quarter"] = raw_df.get("Quarter")
    raw_df["_period_fiscal_year"] = raw_df.get("Fiscal_Year")

    # ------------------------------------------------------------
    # 4. Normalize columns
    # ------------------------------------------------------------
    cur.execute(
    """
    select
        metric_key,
        statement_type_id,
        aggregation_type,
        is_derived,
        allowed_grains
    from metric_definitions;
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

    canonical_df, report = normalize_columns(
        raw_df,
        CANONICAL_FIELDS,
        source_metadata={
            "source": source_type,
            "source_grain": source_grain,
            "is_estimated": is_estimated,
        },
        canonical_metrics=canonical_metrics,
        # llm_mapper=llm_column_mapper,  # No LLM assistance for now
    )
# TEMP FIX: derive period month from canonical period_date
    if "period_date" in canonical_df.columns:
        canonical_df["_period_month"] = canonical_df["period_date"]

    for col in ["_period_month", "_period_quarter", "_period_fiscal_year"]:
        canonical_df[col] = raw_df[col]

    store_validation_issues(company_id, report.get("issues", []))
    # ------------------------------------------------------------
    # 4.5 Detect missing expected metrics (SOFT validation)
    # ------------------------------------------------------------

    # All canonical metric columns present after normalization
    present_metrics = {
        normalize_metric_key(col)
        for col in canonical_df.columns
        if not col.startswith("_")
    }
    cur.execute(
    """
    select
        md.metric_key,
        st.name as statement_name
    from metric_definitions md
    join statement_types st
      on md.statement_type_id = st.id
    where md.metric_key = any(%s);
    """,
    (list(present_metrics),)
    )

    metric_to_statement = dict(cur.fetchall())

    present_metrics_by_statement = defaultdict(set)

    for metric_key, statement_name in metric_to_statement.items():
        present_metrics_by_statement[statement_name.lower()].add(metric_key)

    missing_metric_issues = []

    for statement_name, present_metrics in present_metrics_by_statement.items():
        missing_metric_issues = check_missing_expected_metrics(
            statement_type=statement_name,   # comes from DB
            present_metrics=present_metrics,
            industry=industry_code,       # also from DB
        )
    store_validation_issues(company_id, missing_metric_issues)



    # ------------------------------------------------------------
    # 5. Period type
    # ------------------------------------------------------------
    period_type = (
        "month" if source_grain == "monthly"
        else "quarter" if source_grain == "quarter"
        else "year"
    )

    # ------------------------------------------------------------
    # 6. Insert facts
    # ------------------------------------------------------------
    for _, row in canonical_df.iterrows():

        if row["_period_fiscal_year"] is not None:
            fiscal_year = parse_fiscal_year(row["_period_fiscal_year"])
        else:
            # Fallback: derive from month/date
            fiscal_year = derive_fiscal_year_from_date(
                value=row["_period_month"],
                fiscal_year_start_month=fiscal_year_start_month,
            )
        # -----------------------------
        # 🔹 Grain-correct assignment
        # -----------------------------
        if period_type == "month":
            fiscal_month = extract_calendar_month(row["_period_month"])
            fiscal_quarter = None

        elif period_type == "quarter":
            fiscal_quarter = parse_fiscal_quarter(row["_period_quarter"])
            fiscal_month = None

        else:  # year
            fiscal_month = None
            fiscal_quarter = None

        # -----------------------------
        # Derive period dates
        # -----------------------------
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
            if col.startswith("_") or value is None:
                continue

            metric_key = normalize_metric_key(col)

            cur.execute(
                "select id from metric_definitions where metric_key = %s;",
                (metric_key,),
            )
            row_metric = cur.fetchone()

            if not row_metric:
                continue  # STRICT: no guessing

            metric_id = row_metric[0]

            cur.execute(
                """
                insert into financial_facts (
                    company_id, period_id, metric_id, value, source_system
                )
                values (%s, %s, %s, %s, %s)
                on conflict do nothing;
                """,
                (company_id, period_id, metric_id, value, source_type),
            )

    conn.commit()

    # ------------------------------------------------------------
    # 7. Generate summaries
    # ------------------------------------------------------------
    generate_and_store_monthly_summary(company_id)
    generate_and_store_quarterly_uploaded_summary(company_id)
    generate_and_store_yearly_uploaded_summary(company_id)

    # ------------------------------------------------------------
    # 8. Generate embeddings
    # ------------------------------------------------------------
    embed_missing_summaries(company_id)

    cur.execute(
        """
        update source_documents
        set ingestion_status = 'completed',
            last_processed_at = %s
        where id = %s;
        """,
        (datetime.now(timezone.utc), source_document_id),
    )
    conn.commit()

    cur.close()
    conn.close()

    return {"company_id": company_id, "message": "Ingestion completed"}
