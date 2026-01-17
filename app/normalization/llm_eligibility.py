from typing import Dict, List, Any, Set


# ---------------------------------------------------------------------
# RAW COLUMN ELIGIBILITY (SOURCE SIDE)
# ---------------------------------------------------------------------

_RAW_COLUMN_BLACKLIST_KEYWORDS = {
    "note",
    "notes",
    "comment",
    "comments",
    "remark",
    "remarks",
    "description",
    "narration",
    "text",
    "memo",
}


def is_llm_eligible_raw_column(
    column_name: str,
    pandas_dtype: str | None = None,
) -> bool:
    """
    Structural gate only.
    No financial semantics here.
    """

    if not column_name:
        return False

    name = column_name.lower().strip()

    # 1. Internal / pipeline columns
    if name.startswith("_"):
        return False

    # 2. Obvious non-metric text columns
    for kw in _RAW_COLUMN_BLACKLIST_KEYWORDS:
        if kw in name:
            return False

    # 3. Numeric-only guard (safe & conservative)
    if pandas_dtype:
        if not pandas_dtype.startswith(("int", "float", "decimal")):
            return False

    return True


# ---------------------------------------------------------------------
# CANONICAL METRIC ELIGIBILITY (TARGET SIDE)
# ---------------------------------------------------------------------

def is_llm_eligible_canonical_metric(
    metric: Dict[str, Any],
    source_grain: str,
) -> bool:
    """
    Canonical-side semantic gating.
    Schema is the authority.
    """

    # Must exist
    if not metric.get("metric_key"):
        return False

    # Must support source grain
    allowed_grains = metric.get("allowed_grains") or []
    if source_grain not in allowed_grains:
        return False

    # Aggregation type must be known
    if metric.get("aggregation_type") not in {"sum", "avg", "last", "ratio"}:
        return False

    # Derived metrics are allowed (decision happens later)
    return True


# ---------------------------------------------------------------------
# BUILD PAIRING-BASED LLM CANDIDATES
# ---------------------------------------------------------------------

from typing import Dict, Any, List
import pandas as pd


MAX_SAMPLE_VALUES = 5
MAX_SAMPLE_ROWS = 3


def infer_primitive_type(series: pd.Series) -> str:
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    return "text"


def build_llm_mapping_candidates(
    report: Dict[str, Any],
    raw_df: pd.DataFrame,
    canonical_metrics: List[Dict[str, Any]],
    source_grain: str,
) -> Dict[str, Any]:
    """
    Build rich, SAFE, observational context for LLM-assisted mapping.

    This function:
    - Does NOT decide mappings
    - Does NOT calculate metrics
    - Does NOT infer business meaning
    - ONLY exposes raw evidence
    """

    unmapped_columns = report.get("unmapped", [])
    ambiguous_columns = report.get("ambiguous", [])

    column_context = []

    for col in unmapped_columns:
        if col not in raw_df.columns:
            continue

        series = raw_df[col]

        non_null = series.dropna()

        sample_values = (
            non_null.astype(str)
            .head(MAX_SAMPLE_VALUES)
            .tolist()
        )

        column_context.append({
            "raw_column": col,
            "normalized_column": col.lower().strip(),
            "primitive_type": infer_primitive_type(series),
            "non_null_count": int(non_null.shape[0]),
            "has_percent_symbol": "%" in col.lower(),
            "has_currency_hint": any(
                token in col.lower()
                for token in ["inr", "usd", "rs", "₹", "$"]
            ),
            "sample_values": sample_values,
        })

    sample_rows = (
        raw_df
        .head(MAX_SAMPLE_ROWS)
        .fillna("")
        .astype(str)
        .to_dict(orient="records")
    )

    canonical_metric_context = []

    for m in canonical_metrics:
        canonical_metric_context.append({
            "metric_key": m["metric_key"],
            "display_name": m.get("display_name"),
            "description": m.get("description"),
            "unit": m.get("unit"),
            "aggregation_type": m.get("aggregation_type"),
            "allowed_grains": m.get("allowed_grains"),
            "statement_type": m.get("statement_type"),
        })

    return {
        "source_grain": source_grain,
        "unmapped_columns": column_context,
        "ambiguous_columns": ambiguous_columns,
        "sample_rows": sample_rows,
        "allowed_canonical_metrics": canonical_metric_context,
        "instructions": {
            "rules": [
                "Suggest mappings ONLY if highly confident",
                "Do NOT invent new metrics",
                "Do NOT map percentage columns to absolute metrics",
                "If unsure, return no suggestion",
                "Use sample values and row context to reason",
            ]
        },
    }
