import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv
from app.validations.financial_checks import validate_monthly_financials
from app.validations.store_issues import store_validation_issues



load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# 🔁 Replace with the company_id you just printed
COMPANY_ID = "09b31214-8785-464f-928a-8d2c939db3b8"

# 1. Load CSV
df = pd.read_csv("data/monthly_financials.csv")
issues = validate_monthly_financials(df)
store_validation_issues(COMPANY_ID, issues)

# 2. Connect to Postgres
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

# 3. Insert rows
for _, row in df.iterrows():
    cur.execute(
        insert_sql,
        (
            COMPANY_ID,
            row["Date"],
            row["Revenue"],
            row["COGS"],
            row["Gross_Profit"],
            row["EBITDA"],
            row["Cash_Closing"],
            row["Runway_Months"],
        )
    )

conn.commit()
cur.close()
conn.close()

print("Monthly financials ingested successfully.")
