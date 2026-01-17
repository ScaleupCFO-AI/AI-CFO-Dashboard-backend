from typing import TypedDict, List


class LLMUnmappedColumn(TypedDict):
    raw_column: str
    pandas_dtype: str


class LLMAmbiguousColumn(TypedDict):
    raw_column: str
    candidates: List[str]
    pandas_dtype: str


class LLMCanonicalMetric(TypedDict):
    metric_key: str
    statement_type_id: str
    aggregation_type: str
    is_derived: bool


class LLMMappingInput(TypedDict):
    unmapped: List[LLMUnmappedColumn]
    ambiguous: List[LLMAmbiguousColumn]
    allowed_canonical_metrics: List[LLMCanonicalMetric]

class LLMSuggestedMapping(TypedDict):
    raw_column: str
    canonical_metric: str


class LLMMappingOutput(TypedDict):
    suggestions: List[LLMSuggestedMapping]
