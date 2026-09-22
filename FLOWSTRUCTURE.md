# FLOWSTRUCTURE: Self-Calibrating Current Sensor Fusion Under Thermal Drift

## 1. System Scope & Domain Definition

- **Target Signal:** Electrical Load Current `I(t)` in Amperes [A].
- **Environmental Stressor:** Operating and ambient temperature `T(t)` in Celsius [°C] (ambient shifts + Joule `I^2*R` heating).
- **Sensor Array:** 4 Heterogeneous Current Sensors:
    - **Sensor 1:** Shunt Resistor (TCR thermal gain drift, 0A offset stable).
    - **Sensor 2:** Closed-Loop Hall Sensor A (Temperature-induced DC zero-offset drift).
    - **Sensor 3:** Open-Loop Hall Sensor B (Nonlinear thermal offset + core magnetic saturation).
    - **Sensor 4:** Fluxgate/TMR Sensor (High precision, thermal open-circuit/rail-stick fault mode).

---

## 2. End-to-End Execution Flow

```text
[Raw Multimodal Sensor Streams & Temperature Data]
                            |
                            v
[ Electro-Thermal Preprocessing & Temporal Alignment ]
                            |
                            v
[    Masked Channel Cross-Reconstruction (STAE)      ]
                            |
                            | (Residual Vectors)
                            v
[ Augmented State UKF (Tracking [I, dI/dt, b1..b4])  ]
                            |
                            v
[   Dynamic NIS Covariance Gating (R-inflation)      ]
                            |
                            v
[      Conformal Uncertainty Quantification          ]
                            |
                            v
[           WebSocket Data Broadcast                 ]
                            |
                            v
[             Live React Dashboard                   ]
```

---

## 3. Explicit Directory Tree

```
.
├── configs/
│   └── sensor_specs.yaml
├── src/
│   ├── simulator/
│   │   ├── current_profiles.py
│   │   ├── thermal_engine.py
│   │   └── sensor_array.py
│   ├── models/
│   │   ├── masked_autoencoder.py
│   │   └── conformal_engine.py
│   ├── fusion/
│   │   ├── augmented_ukf.py
│   │   ├── nis_gating.py
│   │   └── pipeline.py
│   └── api/
│       ├── server.py
│       └── schemas.py
├── frontend/
│   └── (React + TypeScript + Tailwind + Recharts/Canvas structure)
└── tests/
    ├── test_thermal_drift.py
    ├── test_gating.py
    └── test_pipeline.py
```

---

## 4. State Machine & Gating Lifecycle

The sensor fusion gating logic transitions through the following states based on the Normalized Innovation Squared (NIS) score of each individual sensor:

- **Healthy**
  - **Condition:** NIS <= 3.84
  - **Action:** Sensor is operating normally within expected thermal bounds. Nominal base covariance (R_base) is applied.

- **Drifting / Re-calibrating**
  - **Condition:** 3.84 < NIS <= 15.0
  - **Action:** Sub-system indicates early signs of thermal drift. Measurement noise covariance is dynamically inflated (R-inflation) to gracefully de-weight the sensor's contribution to the fused state while tracking its bias.

- **Isolated / Hardware Failure**
  - **Condition:** NIS > 15.0
  - **Action:** Abrupt hardware failure, severe saturation, or rail-stick fault detected. Sensor is effectively gated out of the state update by setting R = 1e8.
