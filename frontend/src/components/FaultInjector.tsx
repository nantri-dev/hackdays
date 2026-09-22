import { AlertTriangle, Zap, Thermometer, ShieldAlert, WifiOff, Radio, TrendingUp } from 'lucide-react';
import { useState } from 'react';

interface FaultBtn {
  id: string;
  label: string;
  icon: React.ReactNode;
  color: string;
  sensorId?: number;
  params?: Record<string, unknown>;
}

const FAULT_BUTTONS: FaultBtn[] = [
  // Original sensor faults (original spec names)
  { id: 'hall1_runaway',      label: 'Hall 1 Runaway',      icon: <TrendingUp size={18}/>,  color: 'amber',  sensorId: 1 },
  { id: 'hall2_saturation',   label: 'Hall 2 Saturation',   icon: <ShieldAlert size={18}/>, color: 'crimson', sensorId: 2 },
  { id: 'fluxgate_disconnect',label: 'Fluxgate Disconnect', icon: <WifiOff size={18}/>,     color: 'crimson', sensorId: 3 },
  { id: 'heat_wave',          label: 'Heat Wave (+50°C)',   icon: <Thermometer size={18}/>, color: 'amber'  },
  // New parametric faults
  { id: 'linear_drift',       label: 'Linear Drift',        icon: <TrendingUp size={18}/>,  color: 'amber',  sensorId: 1, params: { ramp_len: 60, rate_pct: 0.5 } },
  { id: 'high_freq_noise',    label: 'High-Freq Noise',     icon: <Radio size={18}/>,       color: 'amber',  sensorId: 0, params: { noise_std: 2.0 } },
  // Utility
  { id: 'bias',               label: 'Bias Drift',          icon: <Zap size={18}/>,         color: 'amber',  sensorId: 1 },
  { id: 'stuck',              label: 'Stuck-At',            icon: <ShieldAlert size={18}/>, color: 'crimson', sensorId: 0 },
];

const COLOR_MAP: Record<string, string> = {
  amber:   'border-amber-700 hover:border-amber-400 hover:text-amber-400',
  crimson: 'border-red-800 hover:border-red-400 hover:text-red-400',
};

export function FaultInjector() {
  const [loading, setLoading] = useState('');

  const injectFault = async (btn: FaultBtn) => {
    setLoading(btn.id);
    const apiBase = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
    const url = `${apiBase.startsWith('http') ? '' : 'http://'}${apiBase}/api/inject_fault`;
    try {
      await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          fault_type: btn.id,
          sensor_id: btn.sensorId ?? 0,
          ...btn.params,
        }),
      });
    } catch (e) {
      console.error(e);
    }
    setLoading('');
  };

  return (
    <div className="bg-card rounded-lg border border-gray-700 h-full flex flex-col p-4 shadow-lg overflow-auto">
      <h3 className="text-gray-400 font-mono text-xs tracking-widest mb-3 flex items-center gap-2">
        <AlertTriangle size={14} className="text-amber-500" /> CHAOS INJECTION
      </h3>

      <div className="grid grid-cols-2 gap-2 flex-grow">
        {FAULT_BUTTONS.map(btn => (
          <button
            key={btn.id}
            onClick={() => injectFault(btn)}
            disabled={loading !== ''}
            className={`bg-[#0b0f19] border ${COLOR_MAP[btn.color] ?? COLOR_MAP.amber} rounded p-2 flex flex-col items-center justify-center gap-1 transition-colors disabled:opacity-40 text-gray-400`}
          >
            {btn.icon}
            <span className="font-mono text-[10px] text-center leading-tight">{btn.label}</span>
          </button>
        ))}
      </div>

      <button
        onClick={() => injectFault({ id: 'reset', label: 'RESET', icon: null, color: 'amber' })}
        disabled={loading !== ''}
        className="mt-3 bg-emerald-500/20 text-emerald-400 border border-emerald-500 rounded py-1.5 font-mono text-xs hover:bg-emerald-500 hover:text-white transition-colors disabled:opacity-40"
      >
        SYS.RESET()
      </button>
    </div>
  );
}
