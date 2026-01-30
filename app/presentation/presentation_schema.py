# app/presentation/presentation_schema.py

from pydantic import BaseModel
from typing import List, Optional, Dict
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
    kpi_intents: Dict[str, IntentEnum] = {}
    time_scope: Optional[str]
