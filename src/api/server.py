import asyncio
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from src.api.schemas import FaultRequest
from src.simulator.current_profiles import CurrentProfile
from src.simulator.thermal_engine import ThermalEngine
from src.simulator.sensor_array import SensorArray
from src.fusion.augmented_ukf import AugmentedUKF
from src.models.conformal_engine import ConformalEngine
from src.diagnostics.residual_tracker import ResidualTracker
from src.diagnostics.fault_classifier import classify_fault_type
from src.diagnostics.disambiguator import disambiguate
from src.diagnostics.gemini_brief import generate_gemini_brief

import numpy as np

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global simulation state ───────────────────────────────────────────────────
current_profile = CurrentProfile()
thermal_engine  = ThermalEngine()
sensor_array    = SensorArray()
ukf             = AugmentedUKF()
conformal       = ConformalEngine()
residual_tracker = ResidualTracker()

T_ambient = 25.0
_heat_wave = False      # group-wide environmental perturbation

# Previous sensor statuses for edge-triggered Gemini calls
_prev_statuses = ["HEALTHY"] * 4
_latest_gemini_brief = None    # cached; pushed on next frame after async resolves
_gemini_lock = asyncio.Lock()  # serialise concurrent brief requests


def _reset_all():
    global current_profile, thermal_engine, sensor_array, ukf, conformal
    global residual_tracker, _prev_statuses, _latest_gemini_brief, _heat_wave
    current_profile  = CurrentProfile()
    thermal_engine   = ThermalEngine()
    sensor_array     = SensorArray()
    ukf              = AugmentedUKF()
    conformal        = ConformalEngine()
    residual_tracker = ResidualTracker()
    _prev_statuses   = ["HEALTHY"] * 4
    _latest_gemini_brief = None
    _heat_wave = False


def _get_sensor_status(r_factor: float, r_base: float) -> str:
    ratio = r_factor / max(r_base, 1e-12)
    if ratio > 1e6:
        return "ISOLATED"
    elif ratio > 1.5:
        return "DRIFTING"
    return "HEALTHY"


@app.post("/api/inject_fault")
async def inject_fault(request: FaultRequest):
    global _heat_wave

    if request.fault_type == "reset":
        _reset_all()
        return {"status": "reset successful"}

    if request.fault_type == "heat_wave":
        _heat_wave = True
        return {"status": "heat_wave activated"}

    # Map named faults to sensor_array targets
    named_targets = {
        "hall1_runaway": 1,
        "hall2_saturation": 2,
        "fluxgate_disconnect": 3,
    }
    target = named_targets.get(request.fault_type, request.sensor_id or 0)

    kwargs = {}
    if request.fault_type == "linear_drift":
        kwargs = {"ramp_len": request.ramp_len, "rate_pct": request.rate_pct}
    elif request.fault_type == "high_freq_noise":
        kwargs = {"noise_std": request.noise_std}

    sensor_array.inject_fault(request.fault_type, target_sensor=target, **kwargs)
    return {"status": f"fault '{request.fault_type}' injected on sensor {target}"}


@app.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    global _prev_statuses, _latest_gemini_brief

    await websocket.accept()
    last_time = time.time()

    try:
        while True:
            # ── Timing ───────────────────────────────────────────────────────
            current_time = time.time()
            dt = current_time - last_time
            if dt < 0.033:
                await asyncio.sleep(0.033 - dt)
                current_time = time.time()
                dt = current_time - last_time
            last_time = current_time

            # ── Physics ──────────────────────────────────────────────────────
            I_true = current_profile.get_current(dt)
            T_eff  = T_ambient + (50.0 if _heat_wave else 0.0)
            T_true = thermal_engine.step(dt, I_true, T_eff)
            raw_sensors, true_biases = sensor_array.read(I_true, T_true)

            # ── UKF Fusion ───────────────────────────────────────────────────
            fused_i, biases, aleatoric, R_diag, trust_scores, fusion_weights = ukf.step(raw_sensors)

            # Conformal uncertainty band
            conformal.update(float(I_true), float(fused_i))
            epistemic = conformal.get_interval()
            total_unc = float(aleatoric) + epistemic

            # ── Residual tracking ─────────────────────────────────────────────
            residual_tracker.update(raw_sensors, fused_i)

            # ── Per-sensor status + fault classification ──────────────────────
            R_base_diag = np.diag(ukf.R_base)
            statuses     = []
            fault_classes = []
            for i in range(4):
                status = _get_sensor_status(R_diag[i], R_base_diag[i])
                statuses.append(status)
                if status in ("DRIFTING", "ISOLATED"):
                    fc = classify_fault_type(residual_tracker.get_window(i))
                else:
                    fc = "Healthy"
                fault_classes.append(fc)

            # ── Multi-sensor disambiguation ───────────────────────────────────
            disam = disambiguate(
                statuses,
                [residual_tracker.get_window(i) for i in range(4)],
                T_true,
                trust_scores,
            )

            # ── Edge-triggered Gemini brief ───────────────────────────────────
            for i in range(4):
                newly_flagged = (
                    statuses[i] in ("DRIFTING", "ISOLATED")
                    and _prev_statuses[i] == "HEALTHY"
                )
                if newly_flagged:
                    window = list(residual_tracker.get_window(i))
                    res_arr = np.array(window) if window else np.zeros(1)
                    traj = list(trust_scores)  # snapshot
                    fault_data = {
                        "sensor_id": i,
                        "fault_class": fault_classes[i],
                        "trust_score": float(trust_scores[i]),
                        "trust_trajectory": [round(v, 3) for v in traj],
                        "disambiguation": disam,
                        "residual_mean": float(res_arr.mean()),
                        "residual_std":  float(res_arr.std()),
                    }
                    # Fire async — do NOT await here (non-blocking)
                    asyncio.create_task(_fetch_and_cache_brief(fault_data))

            _prev_statuses = statuses[:]

            # ── Build and send telemetry frame ────────────────────────────────
            sensors_payload = []
            for i in range(4):
                sensors_payload.append({
                    "raw":          float(raw_sensors[i]),
                    "bias":         float(biases[i]),
                    "corrected":    float(raw_sensors[i] - biases[i]),
                    "r_factor":     float(R_diag[i]),
                    "status":       statuses[i],
                    "trust_score":  float(trust_scores[i]),
                    "fusion_weight": float(fusion_weights[i]),
                    "fault_class":  fault_classes[i],
                })

            frame = {
                "timestamp":     current_time * 1000,
                "temperature":   float(T_true),
                "true_current":  float(I_true),
                "fused_current": float(fused_i),
                "bounds":        [float(fused_i - total_unc), float(fused_i + total_unc)],
                "sensors":       sensors_payload,
                "disambiguation": disam,
                "gemini_brief":  _latest_gemini_brief,
            }

            await websocket.send_json(frame)

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception:
        import traceback
        traceback.print_exc()


async def _fetch_and_cache_brief(fault_data: dict):
    global _latest_gemini_brief
    async with _gemini_lock:
        brief = await generate_gemini_brief(fault_data)
        brief["sensor_id"] = fault_data["sensor_id"]
        _latest_gemini_brief = brief
