from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

class TelemetryIngest(BaseModel):
    # Simplified schema representing incoming telemetry (metrics, logs, traces)
    type: str = Field(..., description="Type of telemetry: metric, log, trace")
    payload: Dict[str, Any]

class AIAnalysisRequest(BaseModel):
    query: str
    time_range: str = "last_15m"

class AIAnalysisResponse(BaseModel):
    tenant_id: str
    issue: str
    root_cause: str
    confidence: float
    suggested_fix: str

class FixRequest(BaseModel):
    suggested_fix: str
    resource_id: Optional[str] = None