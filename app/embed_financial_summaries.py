import psycopg2
import os
from dotenv import load_dotenv

from app.embeddings.generate_embedding import generate_embedding

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


def embed_missing_summaries(company_id: str):
    """
    Generates and stores embeddings for all summaries of a company
    that do not yet have embeddings.

    Deterministic, idempotent, safe to re-run.
    """

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # 1️⃣ Fetch summaries without embeddings
    cur.execute(
        """
        select id, summary_text
        from financial_summaries
        where company_id = %s
          and embedding is null
        """,
        (company_id,)
    )

    summaries = cur.fetchall()

    if not summaries:
        cur.close()
        conn.close()
        return 0

    # 2️⃣ Generate + store embeddings
    for summary_id, summary_text in summaries:
        embedding = generate_embedding(summary_text)
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

    return len(summaries)


# Optional CLI usage for backfills / debugging
if __name__ == "__main__":
    cid = input("Enter company ID: ")
    count = embed_missing_summaries(cid)
    print(f"{count} summaries embedded.")
