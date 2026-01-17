import psycopg2
import os
from dotenv import load_dotenv


def generate_embedding(text: str) -> list[float]:
    """
    Placeholder deterministic embedding.
    Replace with real embedding model later.
    """
    return [0.0] * 1536


load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


def embed_missing_summaries(company_id: str):
    """
    Generate embeddings for summaries that do not yet have one.

    - Reads from financial_summaries.content
    - Writes to summary_embeddings
    - Idempotent
    """

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # ------------------------------------------------------------
    # 1. Fetch summaries without embeddings
    # ------------------------------------------------------------
    cur.execute(
        """
        select
            s.id,
            s.content
        from financial_summaries s
        left join summary_embeddings e
          on s.id = e.summary_id
        where s.company_id = %s
          and e.id is null;
        """,
        (company_id,)
    )

    rows = cur.fetchall()

    if not rows:
        cur.close()
        conn.close()
        return

    # ------------------------------------------------------------
    # 2. Generate and store embeddings
    # ------------------------------------------------------------
    for summary_id, content in rows:
        embedding = generate_embedding(content)

        cur.execute(
            """
            insert into summary_embeddings (
                summary_id,
                embedding
            )
            values (%s, %s);
            """,
            (summary_id, embedding)
        )

    conn.commit()
    cur.close()
    conn.close()
