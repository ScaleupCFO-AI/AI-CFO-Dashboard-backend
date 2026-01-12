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
    mappings = {}
    unmapped = []
    ambiguous = []

    reverse_map = {}  # canonical_field -> source columns

    for src in source_columns:
        best_field = None
        best_score = 0

        for field in canonical_fields:
            for alias in field.aliases:
                score = score_match(src, alias)
                if score > best_score:
                    best_score = score
                    best_field = field

        if best_score >= min_score:
            reverse_map.setdefault(best_field.name, []).append(src)
        else:
            unmapped.append(src)

    # Resolve ambiguity
    for canonical_field, src_cols in reverse_map.items():
        if len(src_cols) == 1:
            mappings[src_cols[0]] = canonical_field
        else:
            ambiguous.extend(src_cols)

    return mappings, unmapped, ambiguous


def normalize_columns(raw_df, canonical_fields, source_metadata):
    source_columns = list(raw_df.columns)

    mappings, unmapped, ambiguous = map_columns(
        source_columns,
        canonical_fields
    )

    canonical_df = raw_df.rename(columns=mappings)

    issues = []

    # 🔹 Unmapped columns → informational
    for col in unmapped:
        issues.append({
            "issue_type": "unmapped_column",
            "column": col,
            "severity": Severity.INFO.value,
            "reason": "Column not part of canonical financial schema"
        })

    # 🔹 Ambiguous columns → high severity (never guess)
    for col in ambiguous:
        issues.append({
            "issue_type": "ambiguous_column",
            "column": col,
            "severity": Severity.HIGH.value,
            "reason": "Column meaning ambiguous; manual resolution required"
        })

    # 🔹 Missing required canonical fields
    for field in canonical_fields:
        if field.required and field.name not in canonical_df.columns:
            issues.append({
                "issue_type": "missing_required_field",
                "column": field.name,
                "severity": Severity.CRITICAL.value,
                "reason": "Required financial field missing after normalization"
            })

    # 🔹 Provenance flags (confidence only)
    provenance_flags = detect_provenance_flags(source_metadata)

    for flag in provenance_flags:
        issues.append({
            "issue_type": "provenance_flag",
            "flag": flag,
            "severity": Severity.MEDIUM.value,
            "reason": f"Data marked as {flag}"
        })

    report = {
        "column_mapping": mappings,
        "issues": issues
    }

    return canonical_df, report
