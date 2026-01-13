import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv

from app.validations.financial_checks import validate_monthly_financials
from app.validations.store_issues import store_validation_issues
from app.normalization.schema_definitions import CANONICAL_FIELDS
from app.normalization.column_mapper import normalize_columns
from app.ingestion.ingest_company import ensure_company_exists

from app.generate_financial_summaries import generate_and_store_monthly_summary
from app.embed_financial_summaries import embed_missing_summaries

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


def ingest_financial_file(
    file_path: str,
    company_name: str,
    source: str = "csv_upload",
    source_grain: str = "monthly",
    is_estimated: bool = False,
):
    """
    End-to-end ingestion pipeline.

    parse
    → normalize
    → validate
    → store canonical facts
    → store validation issues
    → generate derived summaries
    → embed summaries

    - SQL is the source of truth
    - No LLM usage
    - Deterministic and re-runnable
    """

    # 0️⃣ Ensure company exists
    company_id = ensure_company_exists(company_name, source)

    # 1️⃣ Load source file
    if file_path.endswith(".csv"):
        raw_df = pd.read_csv(file_path)
    else:
        raw_df = pd.read_excel(file_path)

    # 2️⃣ Normalize columns to canonical schema
    canonical_df, normalization_report = normalize_columns(
        raw_df,
        CANONICAL_FIELDS,
        source_metadata={
            "source": source,
            "source_grain": source_grain,
            "is_estimated": is_estimated,
        },
    )

    store_validation_issues(company_id, normalization_report["issues"])


    # 3️⃣ Validate canonical data
    validation_issues = validate_monthly_financials(canonical_df)
    store_validation_issues(company_id, validation_issues)

    # 4️⃣ Insert canonical financial facts
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    insert_sql = """
    insert into financial_periods (
        company_id,
        period_date,
        revenue,
        cogs,
        gross_profit,
        ebitda,
        cash_closing,
        runway_months
    )
    values (%s, %s, %s, %s, %s, %s, %s, %s)
    on conflict (company_id, period_date)
    do nothing;
    """

    for _, row in canonical_df.iterrows():
        cur.execute(
            insert_sql,
            (
                company_id,
                row.get("period_date"),
                row.get("revenue"),
                row.get("cogs"),
                row.get("gross_profit"),
                row.get("ebitda"),
                row.get("cash_closing"),
                row.get("runway_months"),
            ),
        )

    conn.commit()
    cur.close()
    conn.close()

    # 5️⃣ Generate and store derived monthly summary (SQL → summary)
    generate_and_store_monthly_summary(company_id)

    # 6️⃣ Generate embeddings for summaries (summary → pgvector)
    embed_missing_summaries(company_id)

    return company_id
