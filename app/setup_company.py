import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute(
    """
    insert into companies (name, source)
    values (%s, %s)
    returning id;
    """,
    ("Restoration Hardware Inc.", "xlsx_upload")
)

company_id = cur.fetchone()[0]

conn.commit()
cur.close()
conn.close()

print("Company ID:", company_id)
