import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv

from app.validations.financial_checks import validate_monthly_financials
from app.validations.store_issues import store_validation_issues

from app.normalization.schema_definitions import CANONICAL_FIELDS
from app.normalization.column_mapper import normalize_columns


load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# 🔁 Replace with the company_id you just printed
COMPANY_ID = "09b31214-8785-464f-928a-8d2c939db3b8"
# COMPANY_ID = "b2f4bbca-f351-43bd-87bb-42d927d4e2bf"  # RH id


# 1️⃣ Load source file
raw_df = pd.read_csv("data/monthly_financials.csv")
# raw_df = pd.read_excel("data/RH_monthly_financials.xlsx")


# 2️⃣ NORMALIZE (NEW STEP — CORE CHANGE)
canonical_df, normalization_report = normalize_columns(
    raw_df,
    CANONICAL_FIELDS,
    source_metadata={
        "source": "csv_upload",      # change to sec_derived / zoho_api later
        "source_grain": "monthly",   # quarterly for RH / SEC
        "is_estimated": False
    }
)

# Store normalization issues (DO NOT BLOCK INGESTION)
store_validation_issues(
    COMPANY_ID,
    normalization_report
)


# 3️⃣ VALIDATE CANONICAL DATA (UNCHANGED LOGIC, BETTER INPUT)
validation_issues = validate_monthly_financials(canonical_df)
store_validation_issues(COMPANY_ID, validation_issues)


# 4️⃣ Connect to Postgres
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


# 5️⃣ Insert CANONICAL rows only
for _, row in canonical_df.iterrows():
    cur.execute(
        insert_sql,
        (
            COMPANY_ID,
            row.get("period_date"),
            row.get("revenue"),
            row.get("cogs"),
            row.get("gross_profit"),
            row.get("ebitda"),
            row.get("cash_closing"),
            row.get("runway_months"),
        )
    )

conn.commit()
cur.close()
conn.close()

print("✅ Monthly financials ingested successfully (normalized + validated).")
