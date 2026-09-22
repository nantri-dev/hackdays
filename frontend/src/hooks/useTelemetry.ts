import { useState, useEffect, useRef } from 'react';

export interface SensorData {
  raw: number;
  bias: number;
  corrected: number;
  r_factor: number;
  status: 'HEALTHY' | 'DRIFTING' | 'ISOLATED';
  trust_score: number;
  fusion_weight: number;
  fault_class: string;
}

export interface GeminiDiagnostic {
  sensor_id: number;
  severity: 'Low' | 'Medium' | 'High' | 'Critical';
  diagnosis: string;
  action_required: string;
  operator_confidence: number;
  source: 'gemini' | 'fallback';
  fallback_reason?: string;
}

export interface TelemetryFrame {
  timestamp: number;
  temperature: number;
  true_current: number;
  fused_current: number;
  bounds: [number, number];
  sensors: SensorData[];
  disambiguation: 'NOMINAL' | 'SENSOR_FAULT' | string;
  gemini_brief: GeminiDiagnostic | null;
  is_online: boolean;
  local_queue_size: number;
}

export function useTelemetry(token: string | null, onAuthError: () => void) {
  const [data, setData] = useState<TelemetryFrame[]>([]);
  const [connected, setConnected] = useState(false);
  const [globalStatus, setGlobalStatus] = useState('NOMINAL');
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!token) return;
    let reconnectTimeout: ReturnType<typeof setTimeout>;

    const connect = () => {
      const apiBase = import.meta.env.VITE_API_URL ?? 'localhost:8000';
      const wsProto = apiBase.startsWith('https') ? 'wss' : 'ws';
      const wsUrl = `${wsProto}://${apiBase.replace(/^https?:\/\//, '')}/ws/telemetry?token=${token}`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        setGlobalStatus('NOMINAL');
      };

      ws.onmessage = (event) => {
        try {
          const raw = JSON.parse(event.data);

          const frame: TelemetryFrame = {
            timestamp:     raw.timestamp,
            temperature:   raw.temperature,
            true_current:  raw.true_current,
            fused_current: raw.fused_current,
            bounds:        raw.bounds,
            disambiguation: raw.disambiguation ?? 'NOMINAL',
            gemini_brief:  raw.gemini_brief ?? null,
            is_online:     raw.is_online ?? true,
            local_queue_size: raw.local_queue_size ?? 0,
            sensors: (raw.sensors as any[]).map((s) => ({
              raw:           s.raw,
              bias:          s.bias,
              corrected:     s.corrected,
              r_factor:      s.r_factor,
              status:        s.status,
              trust_score:   s.trust_score   ?? 1.0,
              fusion_weight: s.fusion_weight ?? 0.25,
              fault_class:   s.fault_class   ?? 'Healthy',
            })),
          };

          let newStatus = 'NOMINAL';
          if (frame.sensors.some(s => s.status === 'ISOLATED')) newStatus = 'DEGRADED / COMPENSATING';
          else if (frame.sensors.some(s => s.status === 'DRIFTING')) newStatus = 'RECALIBRATING';
          setGlobalStatus(newStatus);

          setData(prev => {
            const next = [...prev, frame];
            if (next.length > 150) next.shift();
            return next;
          });
        } catch (e) {
          console.error('Failed to parse telemetry frame', e);
        }
      };

      ws.onclose = (event) => {
        setConnected(false);
        setGlobalStatus('OFFLINE');
        if (event.code === 1008) {
            onAuthError();
        } else {
            reconnectTimeout = setTimeout(connect, 2000);
        }
      };

      ws.onerror = () => ws.close();
    };

    connect();
    return () => {
      clearTimeout(reconnectTimeout);
      wsRef.current?.close();
    };
  }, []);

  return { data, connected, globalStatus };
}
