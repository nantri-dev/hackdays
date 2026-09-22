# Architecture & Flow Structure

## 1. Local Offline-First Physics Loop (30Hz)
- **`current_profiles.py`**: Generates the true current.
- **`thermal_engine.py`**: Simulates temperature based on current.
- **`sensor_array.py`**: Generates 4 readings, adds noise, and injects physical faults (Bias, Gain, Stuck, Noise).
- **`ewma_fusion.py`**: Analyzes the raw readings entirely offline. Flags drift using a median-reference variance test and outputs a fused, clean signal.

## 2. API & Connectivity Layer (`server.py`)
- **Websocket (`/ws/telemetry`)**: Streams the fused data and component statuses to the React frontend.
- **`connectivity.py`**: A background monitor that tracks if the internet connection is active (`is_online`).
- **`local_store.py`**: A lightweight SQLite database (`offline_queue.db`) that durably stores anomaly events if the network goes down.
- **`llm_service.py`**: Contacts Gemini to translate mathematical fault flags into plain-English operator warnings (e.g. "Sensor 1 experienced bias drift").

## 3. The Intermittent Connectivity Lifecycle
1. **Normal Operation**: Sensors fuse locally. If a fault is found, the server fetches a Gemini explanation instantly and streams it to the UI Event Log.
2. **Offline Disconnect**: The user pulls the plug (or simulates it). The fusion engine continues flawlessly at 30Hz because it requires no internet.
3. **Queueing**: A fault occurs offline. Because Gemini cannot be reached, the server generates a templated fallback message ("Explanation pending reconnect") and writes the raw fault data to the SQLite queue.
4. **Reconciliation**: The network connection is restored. A background reconciliation loop detects the `OFFLINE -> ONLINE` transition, iterates over every unsynced row in the SQLite database, fetches the real Gemini explanation, updates the database, and flushes the true AI analysis to the dashboard without dropping any data.
