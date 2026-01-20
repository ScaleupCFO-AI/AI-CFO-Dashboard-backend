from app.presentation.chart_intents import ChartIntent

def resolve_chart_spec(metric: str, intent: ChartIntent, rows: list) -> dict:
    """
    Maps presentation intent → visualization grammar.
    Chart type choice is deterministic and data-driven.
    """

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
        # PIE when showing parts-of-whole at a single point in time
        # STACKED BAR when contribution across periods
        has_multiple_periods = len({r["period_label"] for r in rows}) > 1

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

    raise ValueError(f"Unsupported chart intent: {intent}")
