import re
from app.contracts.severity import Severity
from app.normalization.metadata_flags import detect_provenance_flags


def normalize_text(s: str) -> str:
    return re.sub(r"[^a-z0-9]", " ", s.lower()).strip()


def score_match(source_col, alias):
    s = normalize_text(source_col)
    a = normalize_text(alias)

    if s == a:
        return 100
    if a in s:
        return 70
    if s in a:
        return 60
    return 0


def map_columns(source_columns, canonical_fields, min_score=60):
    mapped = []
    ambiguous = []
    unmapped = []

    reverse_map = {}

    for src in source_columns:
        best_matches = []
        best_score = 0

        for field in canonical_fields:
            for alias in field.aliases:
                score = score_match(src, alias)
                if score > best_score:
                    best_score = score
                    best_matches = [field.name]
                elif score == best_score and score >= min_score:
                    best_matches.append(field.name)

        if best_score < min_score:
            unmapped.append(src)
        elif len(best_matches) == 1:
            mapped.append({
                "raw_column": src,
                "canonical_field": best_matches[0],
            })
        else:
            ambiguous.append({
                "raw_column": src,
                "candidates": best_matches,
            })

    return mapped, ambiguous, unmapped


def normalize_columns(raw_df, canonical_fields, source_metadata):
    source_columns = list(raw_df.columns)

    mapped, ambiguous, unmapped = map_columns(
        source_columns,
        canonical_fields
    )

    rename_map = {
        m["raw_column"]: m["canonical_field"]
        for m in mapped
    }

    canonical_df = raw_df.rename(columns=rename_map)

    issues = []

    for col in unmapped:
        issues.append({
            "issue_type": "unmapped_column",
            "column": col,
            "severity": Severity.INFO.value,
            "description": "Column not part of canonical schema",
        })

    for amb in ambiguous:
        issues.append({
            "issue_type": "ambiguous_column",
            "column": amb["raw_column"],
            "severity": Severity.MEDIUM.value,
            "description": f"Ambiguous mapping candidates: {amb['candidates']}",
        })

    provenance_flags = detect_provenance_flags(source_metadata)
    for flag in provenance_flags:
        issues.append({
            "issue_type": "provenance_flag",
            "severity": Severity.MEDIUM.value,
            "description": f"Data marked as {flag}",
        })

    report = {
        "mapped": mapped,
        "ambiguous": ambiguous,
        "unmapped": unmapped,
        "issues": issues,
    }

    return canonical_df, report
