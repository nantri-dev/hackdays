import numpy as np

def compute_nis_and_adapt_r(innovation, S, R_base, R_current, drift_gate=3.84, fail_gate=15.0):
    """
    Computes Normalized Innovation Squared (NIS) for each sensor
    and dynamically inflates the measurement covariance R.
    """
    N = len(innovation)
    R_adapted = np.copy(R_current)
    
    for i in range(N):
        # NIS_i = nu_i^2 / S_ii
        nis_i = (innovation[i] ** 2) / S[i, i]
        
        if nis_i > fail_gate:
            # Hard failure / isolated
            R_adapted[i, i] = 1e8
        elif nis_i > drift_gate:
            # Drifting - R inflation
            inflation = np.exp(0.5 * (nis_i - drift_gate))
            R_adapted[i, i] = R_base[i, i] * min(inflation, 1e4)
        else:
            # Healthy - decay back to base R
            R_adapted[i, i] = 0.95 * R_adapted[i, i] + 0.05 * R_base[i, i]
            
    return R_adapted
