def extract_available_metrics(summaries: list) -> set[str]:
    """
    Extract canonical metric names from summary content.
    """
    metrics = set()

    for s in summaries:
        content = s.get("content", "")
        for line in content.splitlines():
            line = line.strip()

            # Match lines like: "- Revenue: 1000000"
            if line.startswith("- ") and ":" in line:
                raw_metric = line[2:].split(":", 1)[0]

                normalized = (
                    raw_metric
                    .strip()
                    .lower()
                    .replace(" ", "_")
                )

                metrics.add(normalized)

    return metrics
