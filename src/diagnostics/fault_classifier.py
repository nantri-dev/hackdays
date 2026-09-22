import numpy as np
from collections import deque
from typing import Literal

FaultClass = Literal[
    "Linear Drift",
    "Jitter-Noise",
    "Stuck-At-Flatline",
    "Exponential Runaway",
    "Healthy",
]

_WINDOW = 15   # steps


def classify_fault_type(residual_window: deque) -> FaultClass:
    """
    Classify the fault type of a sensor from its recent residual history.

    Parameters
    ----------
    residual_window : deque of floats — (raw_i - fused_current) for last ≤15 steps.

    Classification rules (per spec):
    - Stuck-At-Flatline : std(window) < 0.05  (near-zero variance)
    - Linear Drift      : monotonic mean shift, moderate variance
                          (monotone fraction of consecutive differences > 0.7, std > 0.02)
    - Exponential Runaway: accelerating deviation — abs(window[-1]) > 3× abs(window[0])
                           AND residuals growing on average
    - Jitter-Noise      : variance spike without sustained mean shift (std high but mean ≈ 0)
    - Healthy           : abs(mean) < 0.2 and std < 0.5

    Returns one of the five strings above.
    """
    if len(residual_window) < 5:
        return "Healthy"

    arr = np.array(list(residual_window))
    mean_r = float(np.mean(arr))
    std_r = float(np.std(arr))
    abs_mean = abs(mean_r)

    if abs_mean < 0.2 and std_r < 0.5:
        return "Healthy"

    # --- Stuck-At-Flatline: variance is tiny
    if std_r < 0.05:
        return "Stuck-At-Flatline"

    # --- Exponential Runaway: accelerating
    if len(arr) >= 8:
        first_half = np.abs(arr[: len(arr) // 2]).mean()
        second_half = np.abs(arr[len(arr) // 2 :]).mean()
        if second_half > 2.5 * first_half + 0.1:
            return "Exponential Runaway"

    # --- Linear Drift: monotonic mean shift
    diffs = np.diff(arr)
    mono_frac = max(
        np.sum(diffs > 0) / len(diffs),
        np.sum(diffs < 0) / len(diffs),
    )
    if mono_frac > 0.65 and abs_mean > 0.3:
        return "Linear Drift"

    # --- Jitter-Noise: high variance, no sustained shift
    if std_r > 1.0 and abs_mean < 1.5:
        return "Jitter-Noise"

    # Default to Linear Drift for any sustained shift not caught above
    if abs_mean > 0.5:
        return "Linear Drift"

    return "Jitter-Noise"
