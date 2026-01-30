from enum import Enum

class ChartIntent(str, Enum):
    TREND = "trend"
    SNAPSHOT = "snapshot"
    COMPARISON = "comparison"
    CONTRIBUTION = "contribution"
    VARIANCE = "variance"
    
