from app.presentation.chart_resolver import resolve_chart_spec
from app.presentation.summary_data_adapter import (
    extract_metric_rows,
    build_chart_data
)
from app.presentation.presentation_schema import PresentationIntent
from app.presentation.available_metrics import extract_available_metrics
from app.presentation.metric_resolution import resolve_metric_or_proxy


def _normalize_metric(name: str) -> str:
    """
    Canonical metric normalization:
    - lowercase
    - spaces → underscores
    """
    return name.strip().lower().replace(" ", "_")


def build_presentation(
    presentation_intent: PresentationIntent,
    summaries: list
) -> dict:

    presentation = {
        "main": {"kpis": [], "charts": []},
        "first_degree": {"kpis": [], "charts": []},
        "second_degree": {"kpis": [], "charts": []},
    }

    print("DEBUG — initial presentation:", presentation)

    # 🔹 Normalize available metrics
    available_metrics_raw = extract_available_metrics(summaries)
    available_metrics = {_normalize_metric(m) for m in available_metrics_raw}

    print("DEBUG — available_metrics (normalized):", available_metrics)

    for section_name in ["main", "first_degree", "second_degree"]:
        metric_intents = getattr(presentation_intent, section_name)

        for mi in metric_intents:
            requested_metric = _normalize_metric(mi.metric)

            print("DEBUG — requested metric:", requested_metric)

            resolved_metric, is_proxy = resolve_metric_or_proxy(
                requested_metric,
                available_metrics
            )

            print("DEBUG — resolved metric:", resolved_metric, "proxy:", is_proxy)

            if not resolved_metric:
                continue  # nothing safe to show

            # 🔹 IMPORTANT: extract rows using the resolved metric
            rows = extract_metric_rows(resolved_metric, summaries)
            print("DEBUG — extracted rows:", rows)

            data, note = build_chart_data(resolved_metric, rows)

            if not data:
                continue

            chart_spec = resolve_chart_spec(resolved_metric, mi.intent, rows)

            presentation[section_name]["kpis"].append(resolved_metric)
            presentation[section_name]["charts"].append({
                "metric": resolved_metric,
                "requested_metric": mi.metric,
                "is_proxy": is_proxy,
                "intent": mi.intent.value,
                "note": "proxy_used" if is_proxy else None,
                **chart_spec,
                "data": data
            })

        print(f"DEBUG — presentation after {section_name}:", presentation)

    return presentation
