from app.presentation.chart_resolver import resolve_chart_spec
from app.presentation.summary_data_adapter import build_chart_data
from app.presentation.fetch_metric_rows import fetch_metric_rows_from_facts

from app.metrics.dependency_graph import load_metric_dependency_graph
from app.metrics.kpi_hierarchy import build_kpi_hierarchy


def _normalize_metric(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def build_presentation(
    presentation_intent,
    summaries: list,          # kept for interface consistency (NOT USED)
    db_conn,
    company_id: str,
) -> dict:
    """
    Build deterministic presentation from SQL facts.

    GUARANTEES:
    - SQL is the single source of truth
    - No summary parsing
    - No LLM inference
    """

    presentation = {
        "main": {"kpis": [], "charts": []},
        "first_degree": {"kpis": [], "charts": []},
        "second_degree": {"kpis": [], "charts": []},
    }

    print("\n[DEBUG] ================= BUILD PRESENTATION =================")
    print("[DEBUG] Root KPIs:", presentation_intent.root_kpis)

    # --------------------------------------------------
    # 1️⃣ Load dependency graph
    # --------------------------------------------------
    dependency_graph = load_metric_dependency_graph(db_conn)
    print("[DEBUG] Dependency graph sample:", list(dependency_graph.items())[:5])

    # --------------------------------------------------
    # 2️⃣ Build KPI hierarchy (BFS)
    # --------------------------------------------------
    normalized_roots = [
        _normalize_metric(k) for k in presentation_intent.root_kpis
    ]

    kpi_hierarchy = build_kpi_hierarchy(
        root_kpis=normalized_roots,
        dependency_graph=dependency_graph,
        max_depth=2,
    )

    print("[DEBUG] KPI hierarchy result:", kpi_hierarchy)

    # --------------------------------------------------
    # 3️⃣ Build charts from FACTS ONLY
    # --------------------------------------------------
    for section in ["main", "first_degree", "second_degree"]:
        metrics = kpi_hierarchy.get(section, [])
        print(f"[DEBUG] Building section '{section}' with metrics:", metrics)

        for metric in metrics:
            metric = _normalize_metric(metric)

            # --------------------------------------------------
            # Fetch rows from financial_facts
            # --------------------------------------------------
            rows = fetch_metric_rows_from_facts(
                conn=db_conn,
                company_id=company_id,
                metric_key=metric,
            )

            print(
                f"[DEBUG][fetch_metric_rows] metric={metric} rows_count={len(rows)}"
            )

            if not rows:
                print(f"[DEBUG] SKIP '{metric}' — no fact rows found")
                continue

            # --------------------------------------------------
            # Build chart-compatible data
            # --------------------------------------------------
            data, reason = build_chart_data(metric, rows)
            print(
                f"[DEBUG][chart_data] metric={metric} reason={reason}"
            )

            if not data:
                print(f"[DEBUG] SKIP '{metric}' — no chartable data")
                continue

            # --------------------------------------------------
            # Resolve intent (metric-specific overrides global)
            # --------------------------------------------------
            metric_intent = (
                presentation_intent.kpi_intents.get(metric)
                if presentation_intent.kpi_intents
                else None
            ) or presentation_intent.intent

            chart_spec = resolve_chart_spec(
                metric=metric,
                intent=metric_intent,
                rows=rows,
            )

            presentation[section]["kpis"].append(metric)
            presentation[section]["charts"].append(
                {
                    "metric": metric,
                    "intent": metric_intent.value if metric_intent else None,
                    **chart_spec,
                    "data": data,
                }
            )

            print(f"[DEBUG] ADDED '{metric}' to section '{section}'")

    print("[DEBUG] FINAL PRESENTATION PAYLOAD:", presentation)
    print("[DEBUG] =======================================================\n")

    return presentation
