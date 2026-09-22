import numpy as np


class TrustScoreTracker:
    """
    Derives and maintains an explicit trust_score per sensor (0.0-1.0)
    from the R adaptation already performed by NIS gating.

    This is a *diagnostic* signal derived from the UKF's internal R inflation.
    It does NOT replace or duplicate the UKF's principled R-based Kalman weighting —
    it simply makes that weighting visible as a human-readable 0–1 score.
    """

    DECAY_FACTOR = 0.80      # trust decays when NIS > drift_gate
    RECOVERY_STEP = 0.05     # trust recovers this much per healthy step
    FLOOR = 0.01             # hard floor so trust never reaches absolute zero

    def __init__(self, n_sensors: int = 4):
        self.trust_scores = np.ones(n_sensors)
        self.n = n_sensors

    def update(self, R_current: np.ndarray, R_base: np.ndarray, drift_gate_ratio: float = 3.84) -> np.ndarray:
        """
        Update trust scores from the current R diagonal vs the base R.

        A sensor is considered 'drifting' this step if its R has been inflated
        (R_current[i,i] > R_base[i,i] * 1.05 tolerance).

        Returns the updated trust_scores array (same reference).
        """
        for i in range(self.n):
            r_ratio = R_current[i, i] / max(R_base[i, i], 1e-12)
            if r_ratio > 1.05:
                # R was inflated this step → decay trust
                self.trust_scores[i] = max(
                    self.FLOOR,
                    self.trust_scores[i] * self.DECAY_FACTOR
                )
            else:
                # Healthy → recover trust
                self.trust_scores[i] = min(1.0, self.trust_scores[i] + self.RECOVERY_STEP)

        return self.trust_scores.copy()

    def softmax_weights(self) -> np.ndarray:
        """
        Expose softmax(trust_scores) as *informational* effective fusion weights.

        IMPORTANT: These weights are diagnostic/explanatory only. The actual UKF
        fusion is driven by R-based Kalman gain (low trust ↔ high R ↔ downweighted),
        not by this softmax. Do not represent these as what the filter computes
        internally — they are a human-readable approximation of the relative trust.
        """
        t = self.trust_scores
        exp_t = np.exp(t - np.max(t))   # numerically stable softmax
        return exp_t / exp_t.sum()

    def reset(self):
        self.trust_scores = np.ones(self.n)
