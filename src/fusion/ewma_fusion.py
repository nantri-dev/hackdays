import numpy as np

class EWMAFusion:
    def __init__(self, num_sensors=4, noise_std=0.1, alpha=0.1, stuck_window=20, stuck_var_threshold=1e-4):
        self.num_sensors = num_sensors
        self.noise_std = noise_std
        
        self.t = 0
        self.ewma_residuals = np.zeros(num_sensors)
        self.baseline_levels = np.zeros(num_sensors)
        self.flags = [False] * num_sensors
        self.estimated_offsets = np.zeros(num_sensors)
        
        self.alpha = alpha
        self.stuck_window = stuck_window
        self.stuck_var_threshold = stuck_var_threshold
        
        self.sensor_history = [[] for _ in range(num_sensors)]
        
    def step(self, raw_sensors):
        # Record history
        for i in range(self.num_sensors):
            self.sensor_history[i].append(raw_sensors[i])
            if len(self.sensor_history[i]) > 300:
                self.sensor_history[i].pop(0)

        # 1. Median Reference
        # Only use unflagged sensors for reference to remain robust
        active_raw = [raw_sensors[i] - self.estimated_offsets[i] for i in range(self.num_sensors) if not self.flags[i]]
        if len(active_raw) == 0:
            active_raw = raw_sensors
        median_ref = np.median(active_raw)

        # 2. EWMA and Flagging
        for i in range(self.num_sensors):
            residual = abs((raw_sensors[i] - self.estimated_offsets[i]) - median_ref)
            self.ewma_residuals[i] = self.alpha * residual + (1 - self.alpha) * self.ewma_residuals[i]

            # Baseline calculation
            if self.t < 100:
                self.baseline_levels[i] += self.ewma_residuals[i] / 100.0
            else:
                # Check drift flag
                if self.ewma_residuals[i] > 3.0 * self.baseline_levels[i] and not self.flags[i]:
                    self.flags[i] = True
                    # Estimate the offset based on median deviation
                    self.estimated_offsets[i] = raw_sensors[i] - median_ref

                # Check stuck flag
                if self.t > self.stuck_window and not self.flags[i]:
                    recent_hist = self.sensor_history[i][-self.stuck_window:]
                    if np.var(recent_hist) < self.stuck_var_threshold:
                        self.flags[i] = True
                        self.estimated_offsets[i] = raw_sensors[i] - median_ref

        # 3. Fusion
        weights = np.zeros(self.num_sensors)
        for i in range(self.num_sensors):
            if not self.flags[i]:
                weights[i] = 1.0 / (self.noise_std ** 2)

        if np.sum(weights) == 0:
            weights = np.ones(self.num_sensors)

        fused = np.average([raw_sensors[i] - self.estimated_offsets[i] for i in range(self.num_sensors)], weights=weights)

        # 4. Confidence Band
        combined_var = 1.0 / np.sum(weights) if np.sum(weights) > 0 else 100.0
        conf_interval = 1.96 * np.sqrt(combined_var)

        self.t += 1
        return fused, self.estimated_offsets, conf_interval, self.flags
