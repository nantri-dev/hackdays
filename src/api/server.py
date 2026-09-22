import asyncio
import time
import sys
import os

# Add parent directory to path to allow src.* imports when running directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from src.api.schemas import FaultRequest
from src.simulator.current_profiles import CurrentProfile
from src.simulator.thermal_engine import ThermalEngine
from src.simulator.sensor_array import SensorArray
from src.fusion.augmented_ukf import AugmentedUKF
from src.models.conformal_engine import ConformalEngine

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
current_profile = CurrentProfile()
thermal_engine = ThermalEngine()
sensor_array = SensorArray()
ukf = AugmentedUKF()
conformal_engine = ConformalEngine()

# Physics loop variables
last_time = time.time()
T_ambient = 25.0

@app.post("/api/inject_fault")
async def inject_fault(request: FaultRequest):
    if request.fault_type == "reset":
        global current_profile, thermal_engine, sensor_array, ukf, conformal_engine
        current_profile = CurrentProfile()
        thermal_engine = ThermalEngine()
        sensor_array = SensorArray()
        ukf = AugmentedUKF()
        conformal_engine = ConformalEngine()
        return {"status": "reset successful"}
        
    sensor_array.inject_fault(request.fault_type)
    return {"status": f"fault {request.fault_type} injected"}

def get_sensor_status(r_factor, r_base):
    ratio = r_factor / r_base
    if ratio > 1000:
        return "ISOLATED"
    elif ratio > 1.2:
        return "DRIFTING"
    else:
        return "HEALTHY"

@app.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    global last_time
    last_time = time.time()
    
    try:
        while True:
            current_time = time.time()
            dt = current_time - last_time
            if dt < 0.033: # Target ~30Hz
                await asyncio.sleep(0.033 - dt)
                current_time = time.time()
                dt = current_time - last_time
                
            last_time = current_time
            
            # 1. Physics Step
            I_true = current_profile.get_current(dt)
            T_true = thermal_engine.step(dt, I_true, T_ambient)
            
            if sensor_array.fault_mode == "heat_wave":
                T_true += 50.0 # Heat wave surge
                
            raw_sensors, true_biases = sensor_array.read(I_true, T_true)
            
            # 2. Fusion Step
            fused_i, est_biases, aleatoric, r_diagonals = ukf.step(raw_sensors)
            
            # 3. Conformal UQ Step
            conformal_engine.update(I_true, fused_i)
            epistemic = conformal_engine.get_interval()
            total_unc = aleatoric + epistemic
            
            # Construct Payload
            sensors = []
            for i in range(4):
                status = get_sensor_status(r_diagonals[i], ukf.R_base[i, i])
                sensors.append({
                    "raw": raw_sensors[i],
                    "bias": est_biases[i],
                    "corrected": raw_sensors[i] - est_biases[i],
                    "r_factor": r_diagonals[i] / ukf.R_base[i, i],
                    "status": status
                })
                
            frame = {
                "timestamp": current_time * 1000,
                "temperature": T_true,
                "true_current": I_true,
                "fused_current": fused_i,
                "bounds": [fused_i - total_unc, fused_i + total_unc],
                "sensors": sensors
            }
            
            await websocket.send_json(frame)
            
    except WebSocketDisconnect:
        print("Client disconnected")
