from collections import deque
import numpy as np

_WINDOW_SIZE = 15


class ResidualTracker:
    """Maintains a per-sensor rolling window of (raw - fused_current) residuals."""

    def __init__(self, n_sensors: int = 4, window: int = _WINDOW_SIZE):
        self.n = n_sensors
        self.buffers = [deque(maxlen=window) for _ in range(n_sensors)]

    def update(self, raw_sensors: np.ndarray, fused_current: float):
        for i in range(self.n):
            self.buffers[i].append(float(raw_sensors[i]) - fused_current)

    def get_window(self, sensor_idx: int) -> deque:
        return self.buffers[sensor_idx]

    def reset(self):
        for buf in self.buffers:
            buf.clear()
