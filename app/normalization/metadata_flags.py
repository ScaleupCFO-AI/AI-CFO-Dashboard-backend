def detect_provenance_flags(source_metadata):
    flags = []

    if source_metadata.get("is_estimated"):
        flags.append("estimated")

    if source_metadata.get("source_grain") != "monthly":
        flags.append("aggregated")

    if source_metadata.get("source") in ["RH", "SEC"]:
        flags.append("external")

    return flags
