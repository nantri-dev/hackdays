import { useState, useEffect } from 'react';
import { Activity, Thermometer, LogOut, Database } from 'lucide-react';
import { CurrentWaveform } from './components/CurrentWaveform';
import { SensorHealthMatrix } from './components/SensorHealthMatrix';
import { FaultInjector } from './components/FaultInjector';
import { BiasTracker } from './components/BiasTracker';
import { DiagnosticBrief } from './components/DiagnosticBrief';
import { useTelemetry } from './hooks/useTelemetry';
import { Login } from './components/Login';

function DisambiguationBanner({ value }: { value: string }) {
  if (value === 'NOMINAL') return null;

  const isEvent = value === 'REAL_EVENT_DETECTED';
  return (
    <div className={`px-4 py-2 rounded font-mono text-xs font-bold tracking-widest border ${
      isEvent
        ? 'bg-sky-900/40 border-sky-500 text-sky-300'
        : 'bg-rose-900/40 border-rose-500 text-rose-300'
    }`}>
      {isEvent ? '🌡 REAL ENV EVENT DETECTED — no individual sensor fault' : '⚠ SENSOR FAULT DETECTED'}
    </div>
  );
}

function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('fusion_auth_token'));

  useEffect(() => {
    if (token) {
      localStorage.setItem('fusion_auth_token', token);
    } else {
      localStorage.removeItem('fusion_auth_token');
    }
  }, [token]);

  const handleLogout = () => {
    setToken(null);
  };

  if (!token) {
    return <Login onLogin={setToken} />;
  }

  return <Dashboard token={token} onLogout={handleLogout} />;
}

function Dashboard({ token, onLogout }: { token: string, onLogout: () => void }) {
  const { data, connected, globalStatus } = useTelemetry(token, onLogout);
  const latest = data.length > 0 ? data[data.length - 1] : null;

  const isOnline = latest?.is_online ?? true;
  const queueSize = latest?.local_queue_size ?? 0;

  return (
    <div className="min-h-screen bg-background text-white p-4 flex flex-col gap-4">
      {/* ── Header ── */}
      <header className="flex justify-between items-center bg-card px-4 py-3 rounded-lg border border-gray-700">
        <div className="flex items-center gap-3">
          <Activity className="text-cyan-400" size={28} />
          <div>
            <h1 className="text-lg font-bold tracking-wider font-mono">FUSION ENGINE</h1>
            <p className="text-xs text-gray-500 font-mono">UKF + NIS Gating + Trust Scoring + Gemini Diagnostics</p>
          </div>
        </div>
        <div className="flex items-center gap-3 flex-wrap justify-end">
          {latest && <DisambiguationBanner value={latest.disambiguation} />}
          {latest && (
            <div className="flex items-center gap-1 text-amber-400 font-mono text-xs bg-card border border-gray-700 px-3 py-1.5 rounded">
              <Thermometer size={14} />
              <span>{latest.temperature.toFixed(1)} °C</span>
            </div>
          )}
          
          {/* Offline/Queue Status */}
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border ${isOnline ? 'bg-emerald-900/20 border-emerald-800' : 'bg-red-900/20 border-red-800'}`}>
            <Database size={12} className={isOnline ? 'text-emerald-500' : 'text-red-500'} />
            <span className={`text-[10px] font-mono ${isOnline ? 'text-emerald-400' : 'text-red-400 animate-pulse'}`}>
              {isOnline ? 'ONLINE' : 'OFFLINE'} | QUEUE: {queueSize}
            </span>
          </div>

          <div className="flex items-center gap-2 bg-[#0b0f19] px-3 py-1.5 rounded-full border border-gray-800">
            <span className={`w-2.5 h-2.5 rounded-full ${connected ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`} />
            <span className="text-[10px] font-mono text-gray-400">WS {connected ? 'ACTIVE' : 'OFFLINE'}</span>
          </div>
          <div className={`px-3 py-1.5 rounded font-bold tracking-widest text-[10px] font-mono ${
            globalStatus === 'NOMINAL'
              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500'
              : 'bg-amber-500/20 text-amber-400 border border-amber-500'
          }`}>
            SYS: {globalStatus}
          </div>
          <button onClick={onLogout} className="p-1.5 rounded bg-gray-800 hover:bg-gray-700 text-gray-400 transition-colors">
            <LogOut size={16} />
          </button>
        </div>
      </header>

      {/* ── Main Grid ── */}
      <main className="grid grid-cols-12 gap-4 flex-grow">

        {/* Left: Waveform + Bias */}
        <section className="col-span-8 flex flex-col gap-4">
          <div className="h-[340px]">
            <CurrentWaveform data={data} />
          </div>
          <div className="h-[260px]">
            <BiasTracker data={data} />
          </div>
        </section>

        {/* Right: Health + Fault Injector + Diagnostic Brief */}
        <section className="col-span-4 flex flex-col gap-4">
          <div className="h-[260px]">
            <SensorHealthMatrix data={data} />
          </div>
          <div className="h-[160px]">
            <FaultInjector token={token} onAuthError={onLogout} />
          </div>
          <div className="flex-grow min-h-[160px]">
            <DiagnosticBrief brief={latest?.gemini_brief ?? null} />
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
