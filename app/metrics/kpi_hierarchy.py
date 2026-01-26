def build_kpi_hierarchy(root_kpis, dependency_graph, max_depth=2):
    """
    root_kpis: ["burn_rate", "runway_months"]

    returns:
    {
      "main": [...],
      "first_degree": [...],
      "second_degree": [...]
    }
    """

    hierarchy = {
        "main": set(),
        "first_degree": set(),
        "second_degree": set(),
    }

    for root in root_kpis:
        visited = {root}
        current = [root]

        hierarchy["main"].add(root)

        for depth in range(1, max_depth + 1):
            next_level = []

            for metric in current:
                for dep in dependency_graph.get(metric, []):
                    if dep not in visited:
                        visited.add(dep)
                        next_level.append(dep)

            if depth == 1:
                hierarchy["first_degree"].update(next_level)
            elif depth == 2:
                hierarchy["second_degree"].update(next_level)

            current = next_level

    # ---- precedence cleanup
    hierarchy["first_degree"] -= hierarchy["main"]
    hierarchy["second_degree"] -= hierarchy["main"]
    hierarchy["second_degree"] -= hierarchy["first_degree"]

    return {
        "main": sorted(hierarchy["main"]),
        "first_degree": sorted(hierarchy["first_degree"]),
        "second_degree": sorted(hierarchy["second_degree"]),
    }
