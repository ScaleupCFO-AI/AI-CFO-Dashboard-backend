def extract_metric_hints(question: str, metric_keys: list[str]) -> list[str]:
    q = question.lower()
    hits = []

    for m in metric_keys:
        if m.replace("_", " ") in q:
            hits.append(m)

    return hits
