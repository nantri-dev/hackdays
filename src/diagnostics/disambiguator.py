import numpy as np
import yaml
from typing import List, Literal

DisambiguationResult = Literal["SENSOR_FAULT", "REAL_EVENT_DETECTED", "NOMINAL"]

# Thermal drift coefficients from sensor_specs.yaml
_THERMAL_DRIFT_COEFFS = [
    0.0,     # shunt — very low thermal sensitivity
    0.06,    # hall_1
    -0.04,   # hall_2
    0.005,   # fluxgate
]

# How much of the observed residual must be explained by thermal drift to call REAL_EVENT
_EXPLANATION_THRESHOLD = 0.5   # 50% of residual explained by temperature


def disambiguate(
    sensor_statuses: List[str],
    residual_windows,
    temperature: float,
    trust_scores: np.ndarray,
) -> DisambiguationResult:
    """
    Determines whether simultaneous sensor anomalies are caused by:
    - A real environmental event (heat_wave / temperature shift) → REAL_EVENT_DETECTED
    - Independent single-sensor faults → SENSOR_FAULT
    - No anomaly → NOMINAL

    Parameters
    ----------
    sensor_statuses  : list of 4 strings ('HEALTHY' / 'DRIFTING' / 'ISOLATED')
    residual_windows : list of 4 deques (raw_i - fused_current)
    temperature      : current temperature reading from ThermalEngine
    trust_scores     : np.ndarray(4,) from TrustScoreTracker

    Logic
    -----
    1. Count flagged sensors (DRIFTING or ISOLATED).
    2. If <2 flagged → SENSOR_FAULT (single-sensor event).
    3. If ≥2 flagged:
       - Compute expected thermal drift for each flagged sensor:
             expected_shift_i = thermal_drift_coeff_i * (T - 25.0)
       - Compare to actual mean residual for each.
       - If most flagged sensors' residuals are largely explained by their own
         thermal_drift_coeff at the current temperature → REAL_EVENT_DETECTED.
       - Otherwise → SENSOR_FAULT (independent failures, not a common cause).
    """
    flagged = [i for i, s in enumerate(sensor_statuses) if s in ("DRIFTING", "ISOLATED")]

    if len(flagged) == 0:
        return "NOMINAL"

    if len(flagged) == 1:
        return "SENSOR_FAULT"

    # ≥ 2 flagged — check if temperature explains it
    dt_temp = temperature - 25.0
    if abs(dt_temp) < 0.5:
        # Temperature hasn't changed — can't be thermal event
        return "SENSOR_FAULT"

    explained_count = 0
    for i in flagged:
        window = residual_windows[i]
        if len(window) < 3:
            continue
        actual_mean = abs(float(np.mean(list(window))))
        expected = abs(_THERMAL_DRIFT_COEFFS[i] * dt_temp)
        if expected > 1e-6 and actual_mean > 1e-6:
            ratio = min(expected, actual_mean) / max(expected, actual_mean)
            if ratio >= _EXPLANATION_THRESHOLD:
                explained_count += 1

    # If more than half the flagged sensors are thermally explained → real event
    if explained_count >= max(1, len(flagged) // 2 + 1):
        return "REAL_EVENT_DETECTED"

    return "SENSOR_FAULT"
