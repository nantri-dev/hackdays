import { useState, useEffect, useRef } from 'react';

export interface SensorData {
  raw: number;
  bias: number;
  corrected: number;
  r_factor: number;
  status: 'HEALTHY' | 'DRIFTING' | 'ISOLATED';
}

export interface TelemetryFrame {
  timestamp: number;
  temperature: number;
  true_current: number;
  fused_current: number;
  bounds: [number, number];
  sensors: SensorData[];
}

export function useTelemetry() {
  const [data, setData] = useState<TelemetryFrame[]>([]);
  const [connected, setConnected] = useState(false);
  const [globalStatus, setGlobalStatus] = useState('NOMINAL');
  const wsRef = useRef<WebSocket | null>(null);
  
  useEffect(() => {
    let reconnectTimeout: any;

    const connect = () => {
      const ws = new WebSocket('ws://localhost:8000/ws/telemetry');
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        setGlobalStatus('NOMINAL');
      };

      ws.onmessage = (event) => {
        const frame: TelemetryFrame = JSON.parse(event.data);
        
        let newStatus = 'NOMINAL';
        const hasIsolated = frame.sensors.some(s => s.status === 'ISOLATED');
        const hasDrifting = frame.sensors.some(s => s.status === 'DRIFTING');
        
        if (hasIsolated) newStatus = 'DEGRADED / COMPENSATING';
        else if (hasDrifting) newStatus = 'RECALIBRATING';
        
        setGlobalStatus(newStatus);
        
        setData(prev => {
          const next = [...prev, frame];
          if (next.length > 150) next.shift(); // sliding window
          return next;
        });
      };

      ws.onclose = () => {
        setConnected(false);
        setGlobalStatus('OFFLINE');
        reconnectTimeout = setTimeout(connect, 2000);
      };

      ws.onerror = (error) => {
        console.error("WebSocket error", error);
        ws.close();
      };
    };

    connect();

    return () => {
      clearTimeout(reconnectTimeout);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return { data, connected, globalStatus };
}
