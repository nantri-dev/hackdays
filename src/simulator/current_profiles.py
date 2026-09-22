import math

class CurrentProfile:
    def __init__(self):
        self.t = 0.0
        
    def get_current(self, dt):
        self.t += dt
        
        # Idle (0-20s)
        if self.t < 20:
            return 0.0
            
        # Cruise (20-60s)
        if self.t < 60:
            return 20.0 + 2.0 * math.sin(self.t)
            
        # Acceleration (60-80s)
        if self.t < 80:
            return 80.0 + 5.0 * math.sin(self.t * 2)
            
        # Regen Braking (80-100s)
        if self.t < 100:
            return -30.0
            
        # Loop
        self.t = 0.0
        return 0.0
