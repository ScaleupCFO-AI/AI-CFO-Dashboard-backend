def _normalize_metric(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def extract_metric_rows(metric: str, summaries: list) -> list[dict]:
    """
    Extract metric values from summary content
    and adapt them to chart-compatible rows.
    """
    metric = _normalize_metric(metric)
    rows = []

    for s in summaries:
        content = s.get("content", "")
        period_date = s.get("period_start")

        # Build a deterministic period label
        period_label = (
            period_date.strftime("%Y-%m")
            if period_date else None
        )

        for line in content.splitlines():
            line = line.strip()

            if line.startswith("- ") and ":" in line:
                raw_metric, raw_value = line[2:].split(":", 1)
                normalized = _normalize_metric(raw_metric)

                DISPLAY_NAME_ALIASES = {
                    "cash_runway_(months)": "runway_months",
                }

                normalized = DISPLAY_NAME_ALIASES.get(normalized, normalized)

                if normalized == metric:
                    rows.append({
                        "period": period_date,
                        "period_label": period_label,
                        "value": raw_value.strip()
                    })


    return rows



def build_chart_data(metric: str, rows: list):
    print(f"[DEBUG][build_chart_data] metric={metric} rows_count={len(rows)}")
    if rows:
        print(f"[DEBUG][build_chart_data] sample_row={rows[0]}")

    if not rows:
        return None, "metric_not_available"

    # --------------------------------------------------
    # 1️⃣ Contribution summaries (DO NOT SORT)
    # --------------------------------------------------
    # Expected shape:
    # { metric, component, value, period_label }
    if "component" in rows[0]:
        return [
            {
                "component": r["component"],
                "value": r["value"],
                "period": r.get("period_label")
            }
            for r in rows
        ], None

    # --------------------------------------------------
    # 2️⃣ Sort time-series rows ASCENDING by period
    # --------------------------------------------------
    rows = sorted(
        rows,
        key=lambda r: r.get("period_label")
    )

    # --------------------------------------------------
    # 3️⃣ Normal time-series
    # --------------------------------------------------
    if len(rows) >= 2:
        return [
            {
                "period": r["period_label"],
                "value": r["value"]
            }
            for r in rows
        ], None

    # --------------------------------------------------
    # 4️⃣ Snapshot fallback (single point)
    # --------------------------------------------------
    return [
        {
            "period": rows[0]["period_label"],
            "value": rows[0]["value"]
        }
    ], "fallback_single_period"
