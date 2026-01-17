from typing import Dict, List, Set


def validate_llm_output(
    llm_output,
    unmapped_columns,
    allowed_metric_keys,
    return_rejections: bool = False,
):
    """
    Deterministically validate LLM mapping suggestions.

    Rules:
    - raw_column must be currently unmapped
    - canonical_metric must exist in metric_definitions
    - Output must match expected schema

    LLM is ADVISORY ONLY.
    """

    validated = []
    rejected = []

    # Guard: malformed output
    if not isinstance(llm_output, dict):
        if return_rejections:
            return validated, [{
                "reason": "llm_output_not_dict",
                "raw_column": None,
                "canonical_metric": None,
            }]
        return validated

    suggestions = llm_output.get("suggestions")
    if not isinstance(suggestions, list):
        if return_rejections:
            return validated, [{
                "reason": "llm_suggestions_not_list",
                "raw_column": None,
                "canonical_metric": None,
            }]
        return validated

    for item in suggestions:
        raw_column = item.get("raw_column")
        canonical_metric = item.get("canonical_metric")

        # -------------------------
        # Schema validation
        # -------------------------
        if not raw_column or not canonical_metric:
            rejected.append({
                "raw_column": raw_column,
                "canonical_metric": canonical_metric,
                "reason": "missing_required_fields",
            })
            continue

        # -------------------------
        # Must be unmapped
        # -------------------------
        if raw_column not in unmapped_columns:
            rejected.append({
                "raw_column": raw_column,
                "canonical_metric": canonical_metric,
                "reason": "column_not_unmapped",
            })
            continue

        # -------------------------
        # Must be a valid metric
        # -------------------------
        if canonical_metric not in allowed_metric_keys:
            rejected.append({
                "raw_column": raw_column,
                "canonical_metric": canonical_metric,
                "reason": "metric_not_in_definitions",
            })
            continue

        # -------------------------
        # Accepted
        # -------------------------
        validated.append({
            "raw_column": raw_column,
            "canonical_metric": canonical_metric,
        })

    if return_rejections:
        return validated, rejected

    return validated
