import psycopg2
import os
from dotenv import load_dotenv

from app.embeddings.generate_embedding import generate_embedding

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# same company id as before
COMPANY_ID = "09b31214-8785-464f-928a-8d2c939db3b8"


def fetch_summaries():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute(
        """
        select id, summary_text
        from financial_summaries
        where company_id = %s
          and embedding is null
        """,
        (COMPANY_ID,)
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return rows


def store_embedding(summary_id, embedding):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    embedding_str = "[" + ",".join(map(str, embedding)) + "]"

    cur.execute(
        """
        update financial_summaries
        set embedding = %s::vector
        where id = %s
        """,
        (embedding_str, summary_id)
    )

    conn.commit()
    cur.close()
    conn.close()



def main():
    summaries = fetch_summaries()

    if not summaries:
        print("No summaries to embed.")
        return

    for summary_id, summary_text in summaries:
        embedding = generate_embedding(summary_text)
        store_embedding(summary_id, embedding)

    print("Embeddings generated and stored.")


if __name__ == "__main__":
    main()
