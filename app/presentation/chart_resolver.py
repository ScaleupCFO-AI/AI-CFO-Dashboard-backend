from app.presentation.chart_intents import ChartIntent


def resolve_chart_spec(metric: str, intent: ChartIntent | None, rows: list) -> dict:
    """
    Maps presentation intent → visualization grammar.
    Chart type choice is deterministic and data-driven.

    SAFETY RULE:
    - intent may be None → default to TREND
    """

    if intent is None:
        print(f"[WARN] Chart intent is None for metric '{metric}'. Defaulting to TREND.")
        intent = ChartIntent.TREND

    if intent == ChartIntent.TREND:
        return {
            "type": "line",
            "x_key": "period",
            "y_keys": ["value"]
        }

    if intent == ChartIntent.SNAPSHOT:
        return {
            "type": "kpi",
            "x_key": None,
            "y_keys": ["value"]
        }

    if intent == ChartIntent.COMPARISON:
        return {
            "type": "bar",
            "x_key": "period",
            "y_keys": ["value"]
        }

    if intent == ChartIntent.CONTRIBUTION:
        has_multiple_periods = len({r.get("period_label") for r in rows}) > 1

        if has_multiple_periods:
            return {
                "type": "stacked_bar",
                "x_key": "period",
                "y_keys": ["value"]
            }
        else:
            return {
                "type": "pie",
                "label_key": "component",
                "value_key": "value"
            }

    if intent == ChartIntent.VARIANCE:
        return {
            "type": "bar",
            "x_key": "period",
            "y_keys": ["value"]
        }

    # FINAL SAFETY NET (never crash API)
    print(f"[ERROR] Unsupported chart intent '{intent}' for metric '{metric}'. Falling back to TREND.")
    return {
        "type": "line",
        "x_key": "period",
        "y_keys": ["value"]
    }
