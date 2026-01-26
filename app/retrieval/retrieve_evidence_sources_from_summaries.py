def retrieve_evidence_sources_from_summaries(conn, summary_ids: list[str]):
    """
    Fetch source documents that actually contributed to the given summaries.
    """

    if not summary_ids:
        return []

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT
                sd.source_type,
                sd.source_name,
                sd.uploaded_at
            FROM summary_sources ss
            JOIN source_documents sd
              ON sd.id = ss.source_document_id
            WHERE ss.summary_id = ANY(%s::uuid[])
            ORDER BY sd.uploaded_at DESC;
            """,
            (summary_ids,),
        )

        rows = cur.fetchall()

    return [
        {
            "source_type": r[0],
            "source_name": r[1],
            "uploaded_at": r[2].isoformat() if r[2] else None,
        }
        for r in rows
    ]
