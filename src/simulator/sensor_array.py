import numpy as np
import yaml

class SensorArray:
    def __init__(self, config_path="configs/sensor_specs.yaml"):
        with open(config_path, "r") as f:
            self.cfg = yaml.safe_load(f)
            
        self.fault_mode = None
        
    def read(self, current, temperature):
        # Base readings
        dt_temp = temperature - 25.0
        
        # 1. Shunt
        alpha = self.cfg['shunt']['alpha']
        y1 = current * (1.0 + alpha * dt_temp)
        
        # 2. Hall 1
        b_drift1 = self.cfg['hall_1']['thermal_drift_coeff'] * dt_temp
        if self.fault_mode == "hall1_runaway":
            b_drift1 += 8.0
        y2 = current + b_drift1
        
        # 3. Hall 2
        b_drift2 = self.cfg['hall_2']['thermal_drift_coeff'] * dt_temp
        I_sat = self.cfg['hall_2']['I_sat']
        if self.fault_mode == "hall2_saturation":
            I_sat = 30.0 # Force severe saturation
        y3 = np.clip(current, -I_sat, I_sat) + b_drift2
        
        # 4. Fluxgate
        y4 = current + self.cfg['fluxgate']['thermal_drift_coeff'] * dt_temp
        if self.fault_mode == "fluxgate_disconnect":
            y4 = 0.0 # Open circuit
            
        # Add noise
        y1 += np.random.normal(0, self.cfg['shunt']['noise_std'])
        y2 += np.random.normal(0, self.cfg['hall_1']['noise_std'])
        y3 += np.random.normal(0, self.cfg['hall_2']['noise_std'])
        
        if self.fault_mode == "fluxgate_disconnect":
            y4 += np.random.normal(0, 10.0) # High noise on disconnect
        else:
            y4 += np.random.normal(0, self.cfg['fluxgate']['noise_std'])
            
        return np.array([y1, y2, y3, y4]), np.array([0.0, b_drift1, b_drift2, 0.0])
        
    def inject_fault(self, fault_type):
        self.fault_mode = fault_type
