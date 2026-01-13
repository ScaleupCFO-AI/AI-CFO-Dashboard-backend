from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class CanonicalField:
    name: str
    required: bool
    data_type: str
    aliases: List[str]


CANONICAL_FIELDS = [
    CanonicalField(
        name="period_date",
        required=True,
        data_type="date",
        aliases=["date", "month", "period", "period end"]
    ),
    CanonicalField(
        name="revenue",
        required=True,
        data_type="numeric",
        aliases=[
            "revenue",
            "total revenue",
            "revenue_total"
            "sales",
            "net sales",
            "turnover"
        ]
    ),
    CanonicalField(
        name="cogs",
        required=False,
        data_type="numeric",
        aliases=[
            "cogs",
            "cogs_",
            "cost of goods sold",
            "cost of sales"
        ]
    ),
    CanonicalField(
        name="ebitda",
        required=False,
        data_type="numeric",
        aliases=[
            "ebitda",
            "ebidta_margin"
            "operating profit",
            "operating income"
        ]
    ),
]
