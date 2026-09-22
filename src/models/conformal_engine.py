import numpy as np

class ConformalEngine:
    def __init__(self, alpha=0.05, window_size=100):
        self.alpha = alpha
        self.window_size = window_size
        self.residuals = []
        
    def update(self, y_true, y_pred):
        # In unsupervised setting, we might use a surrogate for y_true, 
        # but here we'll assume we calibrate on a known healthy subset
        # or use the filter's fused output vs raw sensors
        res = abs(y_true - y_pred)
        self.residuals.append(res)
        if len(self.residuals) > self.window_size:
            self.residuals.pop(0)
            
    def get_interval(self):
        if len(self.residuals) < 10:
            return 1.0 # default fallback
            
        n = len(self.residuals)
        q_idx = int(np.ceil((n + 1) * (1 - self.alpha)))
        q_idx = min(max(q_idx, 1), n) - 1
        
        sorted_res = np.sort(self.residuals)
        return sorted_res[q_idx]
