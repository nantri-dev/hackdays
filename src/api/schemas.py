from pydantic import BaseModel
from typing import List

class FaultRequest(BaseModel):
    fault_type: str

class SensorData(BaseModel):
    raw: float
    bias: float
    corrected: float
    r_factor: float
    status: str

class LLMEvent(BaseModel):
    timestamp: float
    sensor_idx: int
    fault_type: str
    message: str
    is_fallback: bool

class TelemetryFrame(BaseModel):
    timestamp: float
    temperature: float
    true_current: float
    fused_current: float
    bounds: List[float]
    sensors: List[SensorData]
    is_online: bool
    queue_size: int
    events: List[LLMEvent]
