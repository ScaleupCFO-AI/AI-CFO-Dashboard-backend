import psycopg2
import uuid
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


def ensure_company_exists(
    company_name: str,
    source: str = "manual_upload"
) -> str:
    """
    Returns company_id.
    Creates company if it does not exist.
    Deterministic + idempotent.
    """

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # 1️⃣ Check if company already exists
    cur.execute(
        "SELECT id FROM companies WHERE name = %s;",
        (company_name,)
    )
    row = cur.fetchone()

    if row:
        company_id = row[0]
    else:
        company_id = str(uuid.uuid4())
        cur.execute(
            """
            INSERT INTO companies (id, name, source)
            VALUES (%s, %s, %s);
            """,
            (company_id, company_name, source)
        )
        conn.commit()

    cur.close()
    conn.close()

    return company_id
