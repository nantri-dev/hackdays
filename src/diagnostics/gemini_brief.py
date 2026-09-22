import asyncio
import json
import logging
import os

logger = logging.getLogger(__name__)

# Try importing google-genai; if not installed, degrade gracefully.
try:
    from google import genai
    from google.genai import types as genai_types
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False
    logger.warning("google-genai not installed — Gemini briefs will use fallback text.")

SENSOR_NAMES = ["Shunt Resistor", "Hall Sensor A", "Hall Sensor B", "Fluxgate Sensor"]

_FALLBACK_TEMPLATE = (
    "Gemini unavailable. {sensor} is showing {fault_class}. "
    "Trust score: {trust:.2f}. Disambiguation: {disambiguation}. "
    "Manual inspection recommended."
)


async def generate_gemini_brief(fault_data: dict) -> dict:
    """
    Generate a structured diagnostic brief for a sensor fault event.

    fault_data keys:
        sensor_id        : int 0-3
        fault_class      : str (from fault_classifier)
        trust_score      : float 0-1
        trust_trajectory : list[float] last 5 trust scores
        disambiguation   : str SENSOR_FAULT / REAL_EVENT_DETECTED
        residual_mean    : float
        residual_std     : float

    Returns a dict with keys: severity, diagnosis, action_required,
    operator_confidence, source.
    source = "gemini" | "fallback"
    """
    sensor_id = fault_data.get("sensor_id", 0)
    fault_class = fault_data.get("fault_class", "Unknown")
    trust = fault_data.get("trust_score", 1.0)
    disambiguation = fault_data.get("disambiguation", "SENSOR_FAULT")
    sensor_name = SENSOR_NAMES[sensor_id] if sensor_id < 4 else f"Sensor {sensor_id}"

    if not _GENAI_AVAILABLE:
        return _build_fallback(fault_data, sensor_name, reason="google-genai not installed")

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return _build_fallback(fault_data, sensor_name, reason="GEMINI_API_KEY not set")

    prompt = f"""You are an aerospace sensor-fusion diagnostic system.
A sensor anomaly has been detected. Provide a structured JSON diagnostic brief.

Sensor: {sensor_name}
Fault Classification: {fault_class}
Trust Score: {trust:.3f} (1.0=fully trusted, 0.0=isolated)
Trust Trajectory (last 5 steps): {fault_data.get('trust_trajectory', [])}
Disambiguation Result: {disambiguation}
  - SENSOR_FAULT: This sensor alone is failing independently.
  - REAL_EVENT_DETECTED: Multiple sensors drifting due to a real environmental event (e.g. temperature surge) — not a sensor failure.
Residual Mean: {fault_data.get('residual_mean', 0):.3f} A
Residual Std:  {fault_data.get('residual_std', 0):.3f} A

Respond ONLY with valid JSON matching this exact schema:
{{
  "severity": "Low" | "Medium" | "High" | "Critical",
  "diagnosis": "<concise 1-2 sentence plain-English summary>",
  "action_required": "<field-service recommendation>",
  "operator_confidence": <integer 0-100>
}}"""

    try:
        client = genai.Client(api_key=api_key)
        # Run synchronous genai call in a thread to not block async loop
        response = await asyncio.to_thread(
            lambda: client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json",
                ),
            )
        )
        text = response.text.strip()
        brief = json.loads(text)
        brief["source"] = "gemini"
        return brief
    except Exception as exc:
        logger.warning("Gemini call failed: %s", exc)
        return _build_fallback(fault_data, sensor_name, reason=str(exc))


def _build_fallback(fault_data: dict, sensor_name: str, reason: str = "") -> dict:
    trust = fault_data.get("trust_score", 1.0)
    fault_class = fault_data.get("fault_class", "Unknown")
    disambiguation = fault_data.get("disambiguation", "SENSOR_FAULT")

    if trust < 0.2:
        severity = "Critical"
    elif trust < 0.5:
        severity = "High"
    elif trust < 0.8:
        severity = "Medium"
    else:
        severity = "Low"

    if disambiguation == "REAL_EVENT_DETECTED":
        action = "Environmental event confirmed. Monitor all sensors. No individual sensor replacement needed."
    else:
        action = f"Inspect {sensor_name} physically. Consider recalibration or replacement."

    return {
        "severity": severity,
        "diagnosis": (
            f"{sensor_name} exhibits {fault_class}. "
            f"Trust score dropped to {trust:.2f}. "
            f"System verdict: {disambiguation}."
        ),
        "action_required": action,
        "operator_confidence": int(trust * 100),
        "source": "fallback",
        "fallback_reason": reason,
    }
