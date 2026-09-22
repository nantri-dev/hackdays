import asyncio
import time
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.api.schemas import FaultRequest
from src.api.auth import router as auth_router, get_current_user_from_header, _verify_token
from src.simulator.current_profiles import CurrentProfile
from src.simulator.thermal_engine import ThermalEngine
from src.simulator.sensor_array import SensorArray
from src.fusion.augmented_ukf import AugmentedUKF
from src.models.conformal_engine import ConformalEngine
from src.diagnostics.residual_tracker import ResidualTracker
from src.diagnostics.fault_classifier import classify_fault_type
from src.diagnostics.disambiguator import disambiguate
from src.diagnostics.gemini_brief import generate_gemini_brief
from src.database.local_store import LocalStore
from src.connectivity import ConnectivityMonitor

import numpy as np

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

# ── Global simulation state ───────────────────────────────────────────────────
current_profile = CurrentProfile()
thermal_engine  = ThermalEngine()
sensor_array    = SensorArray()
ukf             = AugmentedUKF()
conformal       = ConformalEngine()
residual_tracker = ResidualTracker()
local_store      = LocalStore()
conn_monitor     = ConnectivityMonitor()

T_ambient = 25.0
_heat_wave = False

_prev_statuses = ["HEALTHY"] * 4
_latest_gemini_brief = None    
_gemini_lock = asyncio.Lock()  

def _reset_all():
    global current_profile, thermal_engine, sensor_array, ukf, conformal
    global residual_tracker, _prev_statuses, _latest_gemini_brief, _heat_wave
    current_profile  = CurrentProfile()
    thermal_engine   = ThermalEngine()
    sensor_array     = SensorArray()
    ukf              = AugmentedUKF()
    conformal        = ConformalEngine()
    residual_tracker.reset()
    _prev_statuses   = ["HEALTHY"] * 4
    _latest_gemini_brief = None
    _heat_wave = False
    conn_monitor.reset()
    local_store.clear_all()


def _get_sensor_status(r_factor: float, r_base: float) -> str:
    ratio = r_factor / max(r_base, 1e-12)
    if ratio > 1e6:
        return "ISOLATED"
    elif ratio > 1.5:
        return "DRIFTING"
    return "HEALTHY"


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(conn_monitor.run())
    asyncio.create_task(auto_sync_loop())

async def auto_sync_loop():
    """Background task to sync queued events when connectivity returns."""
    while True:
        await asyncio.sleep(1)
        if conn_monitor.is_online and local_store.get_queue_size() > 0:
            unsynced = local_store.get_unsynced_events()
            for row in unsynced:
                if not conn_monitor.is_online:
                    break
                try:
                    # reconstruct fault_data loosely from stored row
                    fault_data = {
                        "sensor_id": row["sensor_idx"],
                        "fault_class": row["fault_type"],
                        "trust_score": 0.0,
                        "trust_trajectory": [],
                        "disambiguation": "UNKNOWN",
                        "residual_mean": 0.0,
                        "residual_std": 0.0,
                    }
                    brief = await generate_gemini_brief(fault_data)
                    brief["sensor_id"] = fault_data["sensor_id"]
                    
                    # Update local store and broadcast
                    local_store.mark_synced(row["id"], json.dumps(brief))
                    
                    global _latest_gemini_brief
                    _latest_gemini_brief = brief
                except Exception as e:
                    print(f"Failed to sync event {row['id']}: {e}")

@app.post("/api/inject_fault")
async def inject_fault(request: FaultRequest, current_user: str = Depends(get_current_user_from_header)):
    global _heat_wave

    if request.fault_type == "reset":
        _reset_all()
        return {"status": "reset successful"}

    if request.fault_type == "heat_wave":
        _heat_wave = True
        return {"status": "heat_wave activated"}
        
    if request.fault_type == "network_offline":
        conn_monitor.force_offline()
        return {"status": "forced offline"}
        
    if request.fault_type == "network_online":
        conn_monitor.force_online()
        return {"status": "forced online"}

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
async def websocket_endpoint(websocket: WebSocket, token: str = Query(None)):
    if not token:
        await websocket.close(code=1008, reason="Missing token")
        return
    try:
        _verify_token(token)
    except HTTPException:
        await websocket.close(code=1008, reason="Invalid token")
        return

    await websocket.accept()
    last_time = time.time()
    
    global _prev_statuses, _latest_gemini_brief

    try:
        while True:
            current_time = time.time()
            dt = current_time - last_time
            if dt < 0.033:
                await asyncio.sleep(0.033 - dt)
                current_time = time.time()
                dt = current_time - last_time
            last_time = current_time

            I_true = current_profile.get_current(dt)
            T_eff  = T_ambient + (50.0 if _heat_wave else 0.0)
            T_true = thermal_engine.step(dt, I_true, T_eff)
            raw_sensors, true_biases = sensor_array.read(I_true, T_true)

            fused_i, biases, aleatoric, R_diag, trust_scores, fusion_weights = ukf.step(raw_sensors)

            conformal.update(float(I_true), float(fused_i))
            epistemic = conformal.get_interval()
            total_unc = float(aleatoric) + epistemic

            residual_tracker.update(raw_sensors, fused_i)

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

            disam = disambiguate(
                statuses,
                [residual_tracker.get_window(i) for i in range(4)],
                T_true,
                trust_scores,
            )

            for i in range(4):
                newly_flagged = (
                    statuses[i] in ("DRIFTING", "ISOLATED")
                    and _prev_statuses[i] == "HEALTHY"
                )
                if newly_flagged:
                    window = list(residual_tracker.get_window(i))
                    res_arr = np.array(window) if window else np.zeros(1)
                    traj = list(trust_scores)
                    fault_data = {
                        "sensor_id": i,
                        "fault_class": fault_classes[i],
                        "trust_score": float(trust_scores[i]),
                        "trust_trajectory": [round(v, 3) for v in traj],
                        "disambiguation": disam,
                        "residual_mean": float(res_arr.mean()),
                        "residual_std":  float(res_arr.std()),
                    }
                    
                    if conn_monitor.is_online:
                        asyncio.create_task(_fetch_and_cache_brief(fault_data))
                    else:
                        # OFFLINE: Queue it, don't call Gemini
                        fallback = {
                            "sensor_id": i,
                            "severity": "Medium",
                            "diagnosis": f"OFFLINE: {fault_classes[i]} detected. Gemini diagnostic pending reconnect.",
                            "action_required": "Wait for reconnect to sync full diagnostic brief.",
                            "operator_confidence": 50,
                            "source": "fallback"
                        }
                        _latest_gemini_brief = fallback
                        local_store.queue_event(i, fault_classes[i], float(raw_sensors[i]), json.dumps(fallback))

            _prev_statuses = statuses[:]

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
                "is_online":     conn_monitor.is_online,
                "local_queue_size": local_store.get_queue_size(),
            }

            await websocket.send_json(frame)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WS error: {e}")


async def _fetch_and_cache_brief(fault_data: dict):
    global _latest_gemini_brief
    async with _gemini_lock:
        brief = await generate_gemini_brief(fault_data)
        brief["sensor_id"] = fault_data["sensor_id"]
        _latest_gemini_brief = brief

