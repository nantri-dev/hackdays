import numpy as np
import yaml


# Thermal drift coefficients per sensor (from sensor_specs.yaml)
# Used by disambiguator — loaded here to avoid re-opening yaml everywhere.
_THERMAL_DRIFT_COEFFS = None


def _load_coeffs(config_path="configs/sensor_specs.yaml"):
    global _THERMAL_DRIFT_COEFFS
    if _THERMAL_DRIFT_COEFFS is None:
        with open(config_path) as f:
            cfg = yaml.safe_load(f)
        _THERMAL_DRIFT_COEFFS = [
            cfg.get("shunt", {}).get("alpha", 0.0) * cfg.get("shunt", {}).get("R0", 1.0),
            cfg.get("hall_1", {}).get("thermal_drift_coeff", 0.0),
            cfg.get("hall_2", {}).get("thermal_drift_coeff", 0.0),
            cfg.get("fluxgate", {}).get("thermal_drift_coeff", 0.0),
        ]
    return _THERMAL_DRIFT_COEFFS


class SensorArray:
    SENSOR_NAMES = ["shunt", "hall_1", "hall_2", "fluxgate"]

    def __init__(self, config_path="configs/sensor_specs.yaml"):
        with open(config_path, "r") as f:
            self.cfg = yaml.safe_load(f)

        self.fault_mode = None
        self._heat_wave_active = False
        self._heat_wave_delta = 50.0
        # Per-sensor noise std from specs
        self._noise_stds = [
            self.cfg.get("shunt", {}).get("noise_std", 0.08),
            self.cfg.get("hall_1", {}).get("noise_std", 0.15),
            self.cfg.get("hall_2", {}).get("noise_std", 0.20),
            self.cfg.get("fluxgate", {}).get("noise_std", 0.03),
        ]
        # Thermal drift coefficients per sensor
        self._thermal_drift_coeffs = _load_coeffs(config_path)

    def read(self, current, temperature):
        """Return (raw_readings[4], true_biases[4])."""
        dt_temp = temperature - 25.0
        y = np.zeros(4)
        biases = np.zeros(4)

        fm = self.fault_mode
        fm_type = fm.get("type") if fm else None
        fm_target = fm.get("target", 0) if fm else -1
        fm_steps = fm.get("steps", 0) if fm else 0

        for i in range(4):
            # Thermal drift bias (physics-based, applies always)
            thermal_bias = self._thermal_drift_coeffs[i] * dt_temp
            biases[i] = thermal_bias

            # Baseline reading with per-sensor noise
            noise_std = self._noise_stds[i]
            y[i] = current + thermal_bias + np.random.normal(0, noise_std)

            # ----- fault injection -----
            if fm and i == fm_target:
                if fm_type == "hall1_runaway":
                    # Linear/Exponential drift ramping up
                    drift = 8.0 * min(fm_steps / 30.0, 1.0) + 0.1 * fm_steps
                    y[i] += drift
                    biases[i] += drift

                elif fm_type == "hall2_saturation":
                    I_sat = 30.0  # clipped down from 120A
                    y[i] = np.clip(y[i], -I_sat, I_sat)

                elif fm_type == "fluxgate_disconnect":
                    # Reads near 0 with 10× noise
                    y[i] = np.random.normal(0, noise_std * 10.0)

                elif fm_type == "bias":
                    b = 0.05 * fm_steps
                    y[i] += b
                    biases[i] += b

                elif fm_type == "gain":
                    y[i] *= 1.0 + 0.01 * fm_steps

                elif fm_type == "stuck":
                    y[i] = fm.get("stuck_val", current)

                elif fm_type == "noise":
                    y[i] += np.random.normal(0, 5.0)

                elif fm_type == "linear_drift":
                    ramp_len = fm.get("ramp_len", 60)
                    rate_pct = fm.get("rate_pct", 0.5)
                    fraction = min(fm_steps / ramp_len, 1.0)
                    y[i] += current * (rate_pct / 100.0) * fraction
                    biases[i] += current * (rate_pct / 100.0) * fraction

                elif fm_type == "high_freq_noise":
                    extra_std = fm.get("noise_std", 2.0)
                    y[i] += np.random.normal(0, extra_std)

                fm["steps"] += 1

        return y, biases

    def inject_fault(self, fault_type, target_sensor=0, **kwargs):
        """
        Set fault mode. kwargs carries optional params for linear_drift / high_freq_noise.
        heat_wave is handled externally in server.py (T_true offset).
        """
        if fault_type in ("reset", None):
            self.fault_mode = None
        else:
            mode = {
                "type": fault_type,
                "target": target_sensor,
                "steps": 0,
            }
            # Optional parametric fields
            if fault_type == "linear_drift":
                mode["ramp_len"] = kwargs.get("ramp_len", 60)
                mode["rate_pct"] = kwargs.get("rate_pct", 0.5)
            elif fault_type == "high_freq_noise":
                mode["noise_std"] = kwargs.get("noise_std", 2.0)
            elif fault_type == "stuck":
                mode["stuck_val"] = kwargs.get("stuck_val", 0.0)
            self.fault_mode = mode
