from app.presentation.chart_resolver import resolve_chart_spec
from app.presentation.summary_data_adapter import (
    extract_metric_rows,
    build_chart_data
)
from app.presentation.available_metrics import extract_available_metrics
from app.presentation.metric_resolution import resolve_metric_or_proxy

from app.metrics.dependency_graph import load_metric_dependency_graph
from app.metrics.kpi_hierarchy import build_kpi_hierarchy


def _normalize_metric(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def build_presentation(
    presentation_intent,
    summaries: list,
    db_conn
) -> dict:

    presentation = {
        "main": {"kpis": [], "charts": []},
        "first_degree": {"kpis": [], "charts": []},
        "second_degree": {"kpis": [], "charts": []},
    }

    # 1️⃣ Load dependency graph
    dependency_graph = load_metric_dependency_graph(db_conn)

    # 2️⃣ No root KPIs → nothing to show
    if not presentation_intent.root_kpis:
        return presentation

    # 3️⃣ Build KPI hierarchy
    kpi_hierarchy = build_kpi_hierarchy(
        root_kpis=[_normalize_metric(k) for k in presentation_intent.root_kpis],
        dependency_graph=dependency_graph,
        max_depth=2
    )

    # 4️⃣ Normalize available metrics from summaries
    available_metrics_raw = extract_available_metrics(summaries)
    available_metrics = {_normalize_metric(m) for m in available_metrics_raw}

    # 5️⃣ Build charts per section
    for section in ["main", "first_degree", "second_degree"]:
        for metric in kpi_hierarchy.get(section, []):

            resolved_metric, is_proxy = resolve_metric_or_proxy(
                metric,
                available_metrics
            )

            if not resolved_metric:
                continue

            rows = extract_metric_rows(resolved_metric, summaries)
            data, note = build_chart_data(resolved_metric, rows)

            if not data:
                continue

            chart_spec = resolve_chart_spec(
                resolved_metric,
                presentation_intent.intent,
                rows
            )

            presentation[section]["kpis"].append(resolved_metric)
            presentation[section]["charts"].append({
                "metric": resolved_metric,
                "is_proxy": is_proxy,
                "intent": presentation_intent.intent.value if presentation_intent.intent else None,
                "note": "proxy_used" if is_proxy else None,
                **chart_spec,
                "data": data
            })
    print("FINAL PRESENTATION PAYLOAD:", presentation)

    return presentation
