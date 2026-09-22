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
from src.fusion.ewma_fusion import EWMAFusion
from src.database.local_store import LocalStore
from src.connectivity import ConnectivityMonitor
from src.api.llm_service import MockGeminiService

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

current_profile = CurrentProfile()
thermal_engine = ThermalEngine()
sensor_array = SensorArray()
fusion_engine = EWMAFusion()
local_store = LocalStore()
connectivity_monitor = ConnectivityMonitor()
llm_service = MockGeminiService()

last_time = time.time()
T_ambient = 25.0
reported_faults = set() # To track which faults we've already handled

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(connectivity_monitor.run())
    asyncio.create_task(reconciliation_loop())

async def reconciliation_loop():
    """Background task to flush the queue when we reconnect to the internet."""
    was_online = True
    while True:
        is_online = connectivity_monitor.is_online
        
        # Detect transition from offline -> online
        if is_online and not was_online:
            unsynced = local_store.get_unsynced_events()
            for event in unsynced:
                # Generate the real explanation now that we're online
                real_explanation = await llm_service.generate_explanation(
                    event['sensor_idx'], event['fault_type'], event['raw_value']
                )
                local_store.mark_synced(event['id'], real_explanation)
        
        was_online = is_online
        await asyncio.sleep(1.0)

@app.post("/api/inject_fault")
async def inject_fault(request: FaultRequest):
    if request.fault_type == "reset":
        global current_profile, thermal_engine, sensor_array, fusion_engine, reported_faults
        current_profile = CurrentProfile()
        thermal_engine = ThermalEngine()
        sensor_array = SensorArray()
        fusion_engine = EWMAFusion()
        reported_faults.clear()
        local_store.clear_all()
        connectivity_monitor.reset()
        return {"status": "reset successful"}
        
    if request.fault_type == "network_offline":
        connectivity_monitor.force_offline()
        return {"status": "network forced offline"}
        
    if request.fault_type == "network_online":
        connectivity_monitor.force_online()
        return {"status": "network forced online"}
        
    sensor_array.inject_fault(request.fault_type, target_sensor=1) 
    return {"status": f"fault {request.fault_type} injected"}

@app.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    global last_time
    last_time = time.time()
    
    try:
        while True:
            current_time = time.time()
            dt = current_time - last_time
            if dt < 0.033: 
                await asyncio.sleep(0.033 - dt)
                current_time = time.time()
                dt = current_time - last_time
                
            last_time = current_time
            
            # Physics
            I_true = current_profile.get_current(dt)
            T_true = thermal_engine.step(dt, I_true, T_ambient)
            raw_sensors, true_biases = sensor_array.read(I_true, T_true)
            
            # EWMA Fusion
            fused_i, est_biases, conf_interval, flags = fusion_engine.step(raw_sensors)
            
            is_online = connectivity_monitor.is_online
            
            # Process new faults
            for i, is_flagged in enumerate(flags):
                if is_flagged and i not in reported_faults:
                    reported_faults.add(i)
                    fault_type = sensor_array.fault_mode.get('type') if sensor_array.fault_mode else "unknown"
                    
                    if is_online:
                        # Fetch explanation immediately
                        # In reality we wouldn't block the physics loop, but this is mock fast
                        explanation = await llm_service.generate_explanation(i, fault_type, raw_sensors[i])
                        local_store.queue_event(i, fault_type, raw_sensors[i], explanation)
                        
                        # Mark it synced instantly since we did it
                        unsynced = local_store.get_unsynced_events()
                        if unsynced:
                            local_store.mark_synced(unsynced[-1]['id'], explanation)
                    else:
                        # Queue the fallback
                        fallback = f"Sensor {i} drift detected. Gemini explanation pending reconnect..."
                        local_store.queue_event(i, fault_type, raw_sensors[i], fallback)
            
            # Read DB state to send to frontend
            queue_size = local_store.get_queue_size()
            
            events = []
            # Fetch last 5 events
            with __import__('sqlite3').connect(local_store.db_path) as conn:
                conn.row_factory = __import__('sqlite3').Row
                c = conn.cursor()
                c.execute('SELECT * FROM fault_events ORDER BY timestamp DESC LIMIT 5')
                for row in c.fetchall():
                    events.append({
                        "timestamp": row['timestamp'],
                        "sensor_idx": row['sensor_idx'],
                        "fault_type": row['fault_type'],
                        "message": row['llm_explanation'],
                        "is_fallback": row['synced'] == 0
                    })
            
            # Payload construction
            sensors = []
            for i in range(4):
                status = "ISOLATED" if flags[i] else "HEALTHY"
                sensors.append({
                    "raw": float(raw_sensors[i]),
                    "bias": float(est_biases[i]),
                    "corrected": float(raw_sensors[i] - est_biases[i]),
                    "r_factor": 10.0 if flags[i] else 1.0, 
                    "status": status
                })
                
            frame = {
                "timestamp": current_time * 1000,
                "temperature": float(T_true),
                "true_current": float(I_true),
                "fused_current": float(fused_i),
                "bounds": [float(fused_i - conf_interval), float(fused_i + conf_interval)],
                "sensors": sensors,
                "is_online": is_online,
                "queue_size": queue_size,
                "events": events
            }
            
            await websocket.send_json(frame)
            
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error: {e}")
