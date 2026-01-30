"""
Canonical embedding generator for Project Jelly.

- Uses SentenceTransformer (local, deterministic)
- Produces 384-dim embeddings
- HARD FAILS on empty text or bad output
- Safe for ingestion-time usage only
"""

from sentence_transformers import SentenceTransformer
from typing import List
import threading
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


# ------------------------------------------------------------
# MODEL CONFIG (LOCKED)
# ------------------------------------------------------------
MODEL_NAME = "all-MiniLM-L6-v2"
EXPECTED_DIM = 384

# ------------------------------------------------------------
# Singleton model load (important for perf + memory)
# ------------------------------------------------------------
_model = None
_model_lock = threading.Lock()


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                _model = SentenceTransformer(MODEL_NAME)
    return _model


# ------------------------------------------------------------
# Public API (THIS is what ingestion must call)
# ------------------------------------------------------------
def generate_embedding(text: str) -> List[float]:
    """
    Generate a semantic embedding for non-empty summary text.

    GUARANTEES:
    - Never embeds empty text
    - Never returns zero vectors
    - Always returns EXPECTED_DIM floats
    """

    if not text or not text.strip():
        raise ValueError(
            "Refusing to generate embedding for empty or whitespace-only text"
        )

    model = _get_model()

    embedding = model.encode(
        text,
        normalize_embeddings=True,  # cosine-safe, deterministic
    ).tolist()

    # ------------------------------------------------------------
    # HARD GUARDRAILS (NON-NEGOTIABLE)
    # ------------------------------------------------------------
    if len(embedding) != EXPECTED_DIM:
        raise RuntimeError(
            f"Embedding dimension mismatch: "
            f"expected {EXPECTED_DIM}, got {len(embedding)}"
        )

    if all(v == 0.0 for v in embedding):
        raise RuntimeError("Generated embedding is all zeros")

    return embedding

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
