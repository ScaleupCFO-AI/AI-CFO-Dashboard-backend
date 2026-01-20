from typing import List, Optional
from pydantic import BaseModel
from app.presentation.chart_intents import ChartIntent

class MetricIntent(BaseModel):
    metric: str                 # canonical metric name
    intent: ChartIntent
    time_scope: Optional[str] = None  # recent | current | fy

class PresentationIntent(BaseModel):
    main: List[MetricIntent]
    first_degree: List[MetricIntent]
    second_degree: List[MetricIntent]
