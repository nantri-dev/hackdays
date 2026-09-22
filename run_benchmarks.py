import json
import numpy as np
import time
from src.simulator.sensor_array import SensorArray
from src.simulator.current_profiles import CurrentProfile
from src.simulator.thermal_engine import ThermalEngine
from src.fusion.ewma_fusion import EWMAFusion

def run_benchmarks():
    print("Starting EWMA Benchmark...")
    
    current_profile = CurrentProfile()
    thermal_engine = ThermalEngine()
    sensor_array = SensorArray()
    fusion_engine = EWMAFusion()
    
    # Inject bias drift at step 150
    T_ambient = 25.0
    history = []
    
    for t in range(400):
        dt = 0.033
        
        if t == 150:
            sensor_array.inject_fault("bias", target_sensor=1)
            
        I_true = current_profile.get_current(dt)
        T_true = thermal_engine.step(dt, I_true, T_ambient)
        raw_sensors, _ = sensor_array.read(I_true, T_true)
        
        fused_i, _, conf_interval, flags = fusion_engine.step(raw_sensors)
        
        history.append({
            "t": t,
            "truth": I_true,
            "fused": fused_i,
            "naive": np.mean(raw_sensors),
            "conf_lower": fused_i - conf_interval,
            "conf_upper": fused_i + conf_interval,
            "flags": list(flags)
        })

    # Calculate metrics
    truths = np.array([h["truth"] for h in history[150:]])
    fused = np.array([h["fused"] for h in history[150:]])
    naive = np.array([h["naive"] for h in history[150:]])
    
    mae_fused = np.mean(np.abs(truths - fused))
    mae_naive = np.mean(np.abs(truths - naive))
    
    # Detection delay
    flags_s1 = [h["flags"][1] for h in history]
    flag_step = -1
    for i, flagged in enumerate(flags_s1):
        if flagged and i >= 150:
            flag_step = i
            break
            
    delay = flag_step - 150 if flag_step != -1 else -1
    
    # Coverage
    covered = 0
    total = len(history)
    for h in history:
        if h["conf_lower"] <= h["truth"] <= h["conf_upper"]:
            covered += 1
    coverage_pct = (covered / total) * 100
    
    results = {
        "benchmark": "EWMA Sensor Fusion",
        "timestamp": time.time(),
        "mae_fused": float(mae_fused),
        "mae_naive": float(mae_naive),
        "detection_delay_steps": delay,
        "coverage_pct": float(coverage_pct)
    }
    
    with open("artifacts/benchmark_results.json", "w") as f:
        json.dump(results, f, indent=4)
        
    print(json.dumps(results, indent=4))
    
if __name__ == "__main__":
    run_benchmarks()
