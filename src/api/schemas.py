from pydantic import BaseModel
from typing import List, Optional


class FaultRequest(BaseModel):
    fault_type: str
    # Optional params for parametric faults (linear_drift, high_freq_noise)
    sensor_id: Optional[int] = 1
    ramp_len: Optional[int] = 60
    rate_pct: Optional[float] = 0.5
    noise_std: Optional[float] = 2.0


class SensorData(BaseModel):
    raw: float
    bias: float
    corrected: float
    r_factor: float
    status: str
    trust_score: float
    fusion_weight: float
    fault_class: str


class GeminiDiagnostic(BaseModel):
    sensor_id: int
    severity: str
    diagnosis: str
    action_required: str
    operator_confidence: int
    source: str  # "gemini" | "fallback"


class TelemetryFrame(BaseModel):
    timestamp: float
    temperature: float
    true_current: float
    fused_current: float
    bounds: List[float]
    sensors: List[SensorData]
    disambiguation: str      # NOMINAL / SENSOR_FAULT / REAL_EVENT_DETECTED
    gemini_brief: Optional[GeminiDiagnostic] = None
    is_online: bool
    local_queue_size: int
