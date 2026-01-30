def dedupe_with_priority(presentation: dict) -> dict:
    """
    Remove duplicate metrics across sections.
    Priority order: main > first_degree > second_degree
    """
    seen = set()

    for section in ["main", "first_degree", "second_degree"]:
        new_charts = []
        new_kpis = []

        for chart in presentation[section]["charts"]:
            metric = chart["metric"]

            if metric in seen:
                print(f"[DEDUP] Removing '{metric}' from {section}")
                continue

            seen.add(metric)
            new_charts.append(chart)
            new_kpis.append(metric)

        presentation[section]["charts"] = new_charts
        presentation[section]["kpis"] = new_kpis

    return presentation


def section_empty(section: dict) -> bool:
    """
    Section is empty if:
    - no charts
    - OR all charts have empty data
    """
    if not section.get("charts"):
        return True

    for chart in section["charts"]:
        if chart.get("data"):
            return False

    return True


def rebalance_sections(presentation: dict, baseline: dict) -> dict:
    """
    Rebalance sections WITHOUT reintroducing duplicates.
    Empty sections may remain empty.
    """

    # Promote second → first ONLY if first is empty
    if section_empty(presentation["first_degree"]) and not section_empty(presentation["second_degree"]):
        print("[REBALANCE] Promoting second_degree → first_degree")
        presentation["first_degree"] = presentation["second_degree"]
        presentation["second_degree"] = {"kpis": [], "charts": []}

    # Fallback second_degree ONLY if still empty
    if section_empty(presentation["second_degree"]):
        print("[REBALANCE] second_degree empty → baseline fallback")
        presentation["second_degree"] = baseline["second_degree"]

    # Fallback first_degree ONLY if still empty
    if section_empty(presentation["first_degree"]):
        print("[REBALANCE] first_degree empty → baseline fallback")
        presentation["first_degree"] = baseline["first_degree"]

    return presentation
