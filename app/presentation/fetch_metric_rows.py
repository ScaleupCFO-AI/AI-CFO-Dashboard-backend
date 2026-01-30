def fetch_metric_rows_from_facts(
    conn,
    company_id: str,
    metric_key: str,
):
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            p.period_start,
            f.value
        FROM financial_facts f
        JOIN metric_definitions m
          ON f.metric_id = m.id
        JOIN financial_periods p
          ON f.period_id = p.id
        WHERE
            f.company_id = %s
            AND m.metric_key = %s
        ORDER BY p.period_start ASC;
        """,
        (company_id, metric_key),
    )

    rows = cur.fetchall()
    cur.close()

    result = []
    for period_start, value in rows:
        result.append(
            {
                "period_label": period_start.strftime("%Y-%m"),
                "value": value,
            }
        )

    return result
