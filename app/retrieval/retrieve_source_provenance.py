def retrieve_source_provenance(conn, company_id: str):
    """
    Returns source documents used for this company's financial data.
    Deterministic. SQL is the source of truth.
    """

    with conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT
                source_type,
                source_name,
                uploaded_at
            FROM source_documents
            WHERE company_id = %s
            ORDER BY uploaded_at DESC
        """, (company_id,))

        rows = cur.fetchall()

    return [
        {
            "source_type": row[0],
            "source_name": row[1],
            "uploaded_at": row[2].isoformat() if row[2] else None
        }
        for row in rows
    ]
