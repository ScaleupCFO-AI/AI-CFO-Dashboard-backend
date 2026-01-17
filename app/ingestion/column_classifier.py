def classify_raw_column(column_name: str) -> str:
    name = column_name.lower()
    if (
        "%" in name
        or "margin" in name
        or "ratio" in name
        or "yoy" in name
        or "growth" in name
    ):
        return "derived"
    return "raw"
