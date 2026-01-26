from collections import defaultdict

def load_metric_dependency_graph(conn):
    """
    Returns:
    {
      "burn_rate": ["operating_cash_flow"],
      "operating_cash_flow": ["revenue", "operating_expense"],
      ...
    }
    """
    graph = defaultdict(list)

    with conn.cursor() as cur:
        cur.execute("""
            SELECT
              parent.metric_key,
              child.metric_key
            FROM metric_dependencies md
            JOIN metric_definitions parent ON parent.id = md.parent_metric_id
            JOIN metric_definitions child  ON child.id  = md.child_metric_id
        """)

        for parent_key, child_key in cur.fetchall():
            graph[parent_key].append(child_key)

    return dict(graph)
