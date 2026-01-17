import re
import logging
from app.contracts.severity import Severity
from app.normalization.llm_eligibility import build_llm_mapping_candidates
from app.normalization.llm_validation import validate_llm_output
from app.normalization.metadata_flags import detect_provenance_flags

logger = logging.getLogger("column_mapping")


def normalize_text(s: str) -> str:
    """
    Normalize text for deterministic comparison.
    - lowercase
    - remove non-alphanumeric
    - collapse to spaces
    """
    return re.sub(r"[^a-z0-9]", " ", s.lower()).strip()


# ------------------------------------------------------------
# Deterministic matching: EXACT ONLY
# ------------------------------------------------------------
def score_match(source_col: str, alias: str) -> int:
    """
    Deterministic scoring.

    RULE:
    - Only exact normalized matches are allowed.
    - No substring, fuzzy, or semantic matching.

    Returns:
    - 100 for exact match
    - 0 otherwise
    """
    s = normalize_text(source_col)
    a = normalize_text(alias)

    if s == a:
        return 100

    return 0


def map_columns(source_columns, canonical_fields):
    """
    Deterministic column mapping.

    STRICT RULES:
    1. Exact normalized match only → mapped
    2. Multiple exact matches → ambiguous
    3. No exact matches → unmapped
    """

    mapped = []
    ambiguous = []
    unmapped = []

    for src in source_columns:
        matches = []

        for field in canonical_fields:
            for alias in field.aliases:
                if score_match(src, alias) == 100:
                    matches.append(field.name)

        if not matches:
            unmapped.append(src)

        elif len(matches) == 1:
            mapped.append({
                "raw_column": src,
                "canonical_field": matches[0],
            })

        else:
            ambiguous.append({
                "raw_column": src,
                "candidates": matches,
            })

    return mapped, ambiguous, unmapped



def normalize_columns(
    raw_df,
    canonical_fields,
    source_metadata,
    canonical_metrics,   # REQUIRED (schema-backed)
    llm_mapper=None,     # OPTIONAL (advisory only)
):
    source_columns = list(raw_df.columns)

    logger.info(
        "Starting column normalization",
        extra={
            "source_columns": source_columns,
            "source_grain": source_metadata.get("source_grain"),
        },
    )

    # ------------------------------------------------------------
    # 1. Deterministic mapping
    # ------------------------------------------------------------
    mapped, ambiguous, unmapped = map_columns(
        source_columns,
        canonical_fields
    )

    logger.info(
        "Deterministic column mapping completed",
        extra={
            "mapped": mapped,
            "ambiguous": ambiguous,
            "unmapped": unmapped,
        },
    )

    # ------------------------------------------------------------
    # 2. Optional LLM-assisted mapping
    # ------------------------------------------------------------
    llm_output = {"suggestions": []}

    if not llm_mapper:
        logger.info(
            "LLM column mapping skipped",
            extra={
                "reason": "llm_mapper_not_provided",
                "unmapped_columns": unmapped,
            },
        )
    else:
        llm_input = build_llm_mapping_candidates(
            report={
                "mapped": mapped,
                "ambiguous": ambiguous,
                "unmapped": unmapped,
            },
            raw_df=raw_df,
            canonical_metrics=canonical_metrics,
            source_grain=source_metadata["source_grain"],
        )

        logger.info(
            "LLM column mapping invoked",
            extra={
                "llm_input_columns": unmapped,
                "candidate_metric_count": len(canonical_metrics),
            },
        )

        try:
            llm_output = llm_mapper(llm_input) or {"suggestions": []}
        except Exception as e:
            logger.warning(
                "LLM column mapping failed safely",
                extra={
                    "error": str(e),
                },
            )
            llm_output = {"suggestions": []}

        logger.info(
            "LLM column mapping suggestions received | suggestions=%s",
            llm_output.get("suggestions", []),
        )


    # ------------------------------------------------------------
    # 3. Contract-enforced validation of LLM output
    # ------------------------------------------------------------
    allowed_metric_keys = {m["metric_key"] for m in canonical_metrics}

    validated_suggestions, rejected_suggestions = validate_llm_output(
        llm_output=llm_output,
        unmapped_columns=set(unmapped),
        allowed_metric_keys=allowed_metric_keys,
        return_rejections=True,
    )

    for item in validated_suggestions:
        logger.info(
            "LLM column mapping accepted | raw_column=%s | canonical_metric=%s",
            item["raw_column"],
            item["canonical_metric"],
        )


    for item in rejected_suggestions:
        logger.info(
            "LLM column mapping rejected | raw_column=%s | canonical_metric=%s | reason=%s",
            item.get("raw_column"),
            item.get("canonical_metric"),
            item.get("reason"),
        )


    # ------------------------------------------------------------
    # 4. Apply validated LLM mappings
    # ------------------------------------------------------------
    for s in validated_suggestions:
        mapped.append({
            "raw_column": s["raw_column"],
            "canonical_field": s["canonical_metric"],
        })
        unmapped.remove(s["raw_column"])

        # Remove from ambiguous if present
        ambiguous = [
            a for a in ambiguous
            if a.get("raw_column") != s["raw_column"]
        ]

    logger.info(
        "LLM column mapping applied",
        extra={
            "final_mapped_columns": mapped,
            "remaining_unmapped_columns": unmapped,
        },
    )

    # ------------------------------------------------------------
    # 5. Rename dataframe columns
    # ------------------------------------------------------------
    rename_map = {
        m["raw_column"]: m["canonical_field"]
        for m in mapped
    }

    canonical_df = raw_df.rename(columns=rename_map)

    # ------------------------------------------------------------
    # 6. Validation issues
    # ------------------------------------------------------------
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

    logger.info(
        "Column normalization completed",
        extra={
            "total_mapped": len(mapped),
            "total_unmapped": len(unmapped),
            "total_issues": len(issues),
        },
    )

    report = {
        "mapped": mapped,
        "ambiguous": ambiguous,
        "unmapped": unmapped,
        "issues": issues,
    }

    return canonical_df, report
