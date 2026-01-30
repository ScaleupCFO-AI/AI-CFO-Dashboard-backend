import hashlib


def compute_file_hash(file_path: str) -> str:
    """
    Compute SHA256 hash of file contents.
    This is the true identity of an uploaded file.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def normalize_metric_key(col: str) -> str:
    """
    Normalize metric keys to avoid duplicates.
    """
    return (
        col.strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


def get_or_create_source_document(
    cur,
    company_id: str,
    file_hash: str,
    source_type: str,
    source_name: str,
):
    """
    Register or fetch ingestion job for a file.

    source_name = INTERNAL filename (temp / stored name)
    original_filename is attached later in upload route
    """
    cur.execute(
        """
        SELECT id, ingestion_status
        FROM source_documents
        WHERE company_id = %s AND file_hash = %s;
        """,
        (company_id, file_hash),
    )
    row = cur.fetchone()

    if row:
        return {"id": row[0], "status": row[1], "is_new": False}

    cur.execute(
        """
        INSERT INTO source_documents (
            company_id,
            source_type,
            source_name,
            file_hash,
            ingestion_status
        )
        VALUES (%s, %s, %s, %s, 'uploaded')
        RETURNING id;
        """,
        (company_id, source_type, source_name, file_hash),
    )

    return {"id": cur.fetchone()[0], "status": "uploaded", "is_new": True}



def get_or_create_period(
    cur,
    company_id,
    period_start,
    period_end,
    period_type,
    fiscal_year,
    fiscal_quarter,
    fiscal_month,
):

    """
    Period uniqueness = (company_id, period_start, period_type)
    """
    cur.execute(
        """
        select id from financial_periods
        where company_id = %s
          and period_start = %s
          and period_type = %s;
        """,
        (company_id, period_start, period_type),
    )
    row = cur.fetchone()
    if row:
        return row[0]

    cur.execute(
        """
        insert into financial_periods (
            company_id,
            period_start,
            period_end,
            period_type,
            fiscal_year,
            fiscal_quarter,
            fiscal_month
        )
        values (%s, %s, %s, %s, %s, %s, %s)
        returning id;
        """,
        (
            company_id,
            period_start,
            period_end,
            period_type,
            fiscal_year,
            fiscal_quarter,
            fiscal_month
        ),
    )
    return cur.fetchone()[0]


def get_or_create_metric(
    cur,
    metric_key: str,
    display_name: str,
    statement_type_id: str,
):
    """
    Metric uniqueness is GLOBAL by metric_key.
    """
    cur.execute(
        "select id from metric_definitions where metric_key = %s;",
        (metric_key,),
    )
    row = cur.fetchone()
    if row:
        return row[0]

    cur.execute(
        """
        insert into metric_definitions (
            metric_key,
            display_name,
            statement_type_id
        )
        values (%s, %s, %s)
        returning id;
        """,
        (metric_key, display_name, statement_type_id),
    )
    return cur.fetchone()[0]
