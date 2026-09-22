import numpy as np
from filterpy.kalman import MerweScaledSigmaPoints
from filterpy.kalman import UnscentedKalmanFilter as UKF
from .nis_gating import compute_nis_and_adapt_r

def fx(x, dt):
    # State transition function
    # x = [I_load, dI/dt, b1, b2, b3, b4]
    F = np.eye(6)
    F[0, 1] = dt  # I(t) = I(t-1) + dI/dt * dt
    # Biases follow random walk, so b(t) = b(t-1)
    return np.dot(F, x)

def hx(x):
    # Measurement function
    # y = [I_load + b1, I_load + b2, I_load + b3, I_load + b4]
    I_load = x[0]
    biases = x[2:]
    return np.array([I_load + b for b in biases])

class AugmentedUKF:
    def __init__(self, dt=0.033, R_base=None):
        self.dt = dt
        
        if R_base is None:
            # Default base covariance from specs
            self.R_base = np.diag([0.08**2, 0.15**2, 0.2**2, 0.03**2])
        else:
            self.R_base = R_base
            
        self.R_current = np.copy(self.R_base)
        
        # State dimension n=6, Measurement dimension m=4
        points = MerweScaledSigmaPoints(n=6, alpha=1e-3, beta=2, kappa=0)
        self.ukf = UKF(dim_x=6, dim_z=4, fx=fx, hx=hx, dt=dt, points=points)
        
        # Initial state
        self.ukf.x = np.zeros(6)
        
        # Initial error covariance P
        self.ukf.P = np.eye(6) * 1.0
        
        # Process noise Q
        self.ukf.Q = np.eye(6)
        self.ukf.Q[0, 0] = 0.1   # I_load variance
        self.ukf.Q[1, 1] = 1.0   # dI/dt variance
        for i in range(2, 6):
            self.ukf.Q[i, i] = 1e-4  # Bias random walk variance
            
        self.ukf.R = np.copy(self.R_base)
        
    def step(self, z):
        # Predict step
        self.ukf.predict()
        
        # Compute Innovation for NIS gating
        y_pred = hx(self.ukf.x)
        innovation = z - y_pred
        
        # Compute S (Innovation covariance)
        # S = H P H^T + R. Since hx is linear with respect to x, H = [[1, 0, 1, 0, 0, 0], [1, 0, 0, 1, 0, 0], ...]
        H = np.zeros((4, 6))
        H[:, 0] = 1.0
        for i in range(4):
            H[i, i+2] = 1.0
            
        S = np.dot(H, np.dot(self.ukf.P, H.T)) + self.R_current
        
        # Adapt R using NIS
        self.R_current = compute_nis_and_adapt_r(innovation, S, self.R_base, self.R_current)
        
        # Apply updated R to UKF
        self.ukf.R = np.copy(self.R_current)
        
        # Update step
        self.ukf.update(z)
        
        # Returns: fused current, biases array, aleatoric uncertainty, R diagonal
        aleatoric = np.sqrt(self.ukf.P[0, 0])
        return self.ukf.x[0], self.ukf.x[2:6], aleatoric, np.diag(self.R_current)
