import numpy as np
from filterpy.kalman import MerweScaledSigmaPoints
from filterpy.kalman import UnscentedKalmanFilter as UKF
from .nis_gating import compute_nis_and_adapt_r
from .trust import TrustScoreTracker


def fx(x, dt):
    # State transition: x = [I_load, dI/dt, b1, b2, b3, b4]
    F = np.eye(6)
    F[0, 1] = dt
    return np.dot(F, x)


def hx(x):
    # Measurement model: y_i = I_load + b_i
    I_load = x[0]
    biases = x[2:]
    return np.array([I_load + b for b in biases])


class AugmentedUKF:
    def __init__(self, dt=0.033, R_base=None):
        self.dt = dt

        if R_base is None:
            self.R_base = np.diag([0.08**2, 0.15**2, 0.2**2, 0.03**2])
        else:
            self.R_base = R_base

        self.R_current = np.copy(self.R_base)

        points = MerweScaledSigmaPoints(n=6, alpha=1e-3, beta=2, kappa=0)
        self.ukf = UKF(dim_x=6, dim_z=4, fx=fx, hx=hx, dt=dt, points=points)

        self.ukf.x = np.zeros(6)
        self.ukf.P = np.eye(6) * 1.0
        self.ukf.Q = np.eye(6)
        self.ukf.Q[0, 0] = 0.1
        self.ukf.Q[1, 1] = 1.0
        for i in range(2, 6):
            self.ukf.Q[i, i] = 1e-4
        self.ukf.R = np.copy(self.R_base)

        # Trust score tracker — derives from R inflation, does NOT drive the filter
        self.trust_tracker = TrustScoreTracker(n_sensors=4)

    def step(self, z):
        """
        Run one UKF predict-update cycle.

        Returns
        -------
        fused_current : float
        biases        : np.ndarray (4,)
        aleatoric     : float  — sqrt(P[0,0])
        R_diag        : np.ndarray (4,) — diagonal of adapted R
        trust_scores  : np.ndarray (4,) — smoothed 0-1 trust per sensor
        fusion_weights: np.ndarray (4,) — softmax(trust_scores), diagnostic only
        """
        self.ukf.predict()

        y_pred = hx(self.ukf.x)
        innovation = z - y_pred

        H = np.zeros((4, 6))
        H[:, 0] = 1.0
        for i in range(4):
            H[i, i + 2] = 1.0

        S = np.dot(H, np.dot(self.ukf.P, H.T)) + self.R_current

        self.R_current = compute_nis_and_adapt_r(
            innovation, S, self.R_base, self.R_current
        )
        self.ukf.R = np.copy(self.R_current)
        self.ukf.update(z)

        aleatoric = float(np.sqrt(self.ukf.P[0, 0]))

        # Update trust scores from R inflation (diagnostic, not filter input)
        trust_scores = self.trust_tracker.update(self.R_current, self.R_base)
        fusion_weights = self.trust_tracker.softmax_weights()

        return (
            float(self.ukf.x[0]),
            self.ukf.x[2:6].copy(),
            aleatoric,
            np.diag(self.R_current).copy(),
            trust_scores,
            fusion_weights,
        )

    def reset(self):
        self.ukf.x = np.zeros(6)
        self.ukf.P = np.eye(6) * 1.0
        self.ukf.R = np.copy(self.R_base)
        self.R_current = np.copy(self.R_base)
        self.trust_tracker.reset()
