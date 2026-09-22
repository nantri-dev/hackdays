import asyncio

class MockGeminiService:
    def __init__(self):
        pass
        
    async def generate_explanation(self, sensor_idx, fault_type, raw_value):
        # Simulate network delay for API call
        await asyncio.sleep(0.5)
        
        sensor_names = ["Shunt", "Hall 1", "Hall 2", "Fluxgate"]
        name = sensor_names[sensor_idx]
        
        # Real-sounding explanation
        if fault_type == "bias":
            return f"The {name} sensor exhibited a gradual baseline shift, typical of thermal drift. The EWMA filter detected this deviation and successfully isolated the sensor to preserve the fused estimate."
        elif fault_type == "gain":
            return f"The {name} sensor showed a multiplicative error (gain drift). This usually indicates a calibration issue or core saturation. It has been isolated."
        elif fault_type == "stuck":
            return f"The {name} sensor's readings became unnaturally static. This indicates a physical disconnect or ADC freeze. The sensor is now excluded from fusion."
        else:
            return f"The {name} sensor experienced extreme noise spikes. It has been temporarily isolated until the variance normalizes."
