import psycopg2
from app.db.connection import get_db_connection

def get_all_metric_keys() -> list[str]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT metric_key FROM metric_definitions;"
            )
            return [r[0] for r in cur.fetchall()]
    finally:
        conn.close()
