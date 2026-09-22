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
        
        # We will keep the original noise configs but apply the new fault injection logic cleanly.
        y = np.zeros(4)
        biases = np.zeros(4)
        
        for i in range(4):
            y[i] = current + np.random.normal(0, 0.1) # uniform noise std
            
            if self.fault_mode:
                target_sensor = self.fault_mode.get('target', 0)
                f_type = self.fault_mode.get('type')
                steps_active = self.fault_mode.get('steps', 0)
                
                if i == target_sensor:
                    if f_type == "bias":
                        biases[i] = 0.05 * steps_active
                        y[i] += biases[i]
                    elif f_type == "gain":
                        y[i] *= (1.0 + 0.01 * steps_active)
                    elif f_type == "stuck":
                        # For stuck, we just return 0 for simplicity or a fixed value if tracking history
                        y[i] = self.fault_mode.get('stuck_val', current)
                    elif f_type == "noise":
                        y[i] += np.random.normal(0, 5.0)
                        
                    self.fault_mode['steps'] += 1
                    
        return y, biases
        
    def inject_fault(self, fault_type, target_sensor=0):
        if fault_type == "reset":
            self.fault_mode = None
        else:
            self.fault_mode = {
                'type': fault_type,
                'target': target_sensor,
                'steps': 0
            }
