class ThermalEngine:
    def __init__(self, R_th=0.1, tau_th=50.0):
        self.T = 25.0
        self.R_th = R_th
        self.tau_th = tau_th
        
    def step(self, dt, current, T_ambient):
        # dT/dt = (R_th / tau_th) * I(t)^2 - (1 / tau_th) * (T(t) - T_ambient(t))
        heating = (self.R_th / self.tau_th) * (current ** 2)
        cooling = (1.0 / self.tau_th) * (self.T - T_ambient)
        dT = (heating - cooling) * dt
        self.T += dT
        return self.T
