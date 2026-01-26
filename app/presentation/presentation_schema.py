from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class IntentEnum(str, Enum):
    trend = "trend"
    snapshot = "snapshot"
    comparison = "comparison"
    contribution = "contribution"
    variance = "variance"


class PresentationIntent(BaseModel):
    root_kpis: List[str]
    intent: Optional[IntentEnum]
    time_scope: Optional[str]
