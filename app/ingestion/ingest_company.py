import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


def extract_domain(email: str) -> str:
    """
    Extracts domain from email.
    Example: finance@acme.com → acme.com
    """
    return email.split("@")[-1].lower().strip()


def ensure_company_exists(
    company_email: str,
    company_name: str | None = None,
    industry_code: str | None = None,
    base_currency: str = "INR",
    fiscal_year_start_month: int = 4,
) -> str:
    """
    Returns company_id.
    Company identity is determined by email domain.
    Deterministic + idempotent.
    """

    company_domain = extract_domain(company_email)

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # 1️⃣ Check if company already exists by domain
    cur.execute(
        "select id from companies where company_domain = %s;",
        (company_domain,)
    )
    row = cur.fetchone()

    if row:
        company_id = row[0]
    else:
        cur.execute(
            """
            insert into companies (
                name,
                company_domain,
                industry_code,
                base_currency,
                fiscal_year_start_month
            )
            values (%s, %s, %s, %s, %s)
            returning id;
            """,
            (
                company_name or company_domain,
                company_domain,
                industry_code,
                base_currency,
                fiscal_year_start_month,
            )
        )
        company_id = cur.fetchone()[0]
        conn.commit()

    cur.close()
    conn.close()

    return company_id
