import { useTelemetry } from './hooks/useTelemetry';
import { CurrentWaveform } from './components/CurrentWaveform';
import { SensorHealthMatrix } from './components/SensorHealthMatrix';
import { BiasTracker } from './components/BiasTracker';
import { FaultInjector } from './components/FaultInjector';
import { Activity, Thermometer } from 'lucide-react';

function App() {
  const { data, connected, globalStatus } = useTelemetry();

  const latestTemp = data.length > 0 ? data[data.length - 1].temperature.toFixed(1) : '--';
  const latestCurrent = data.length > 0 ? data[data.length - 1].fused_current.toFixed(2) : '--';

  return (
    <div className="min-h-screen bg-background text-white p-6 flex flex-col gap-6">
      {/* Top Bar */}
      <header className="flex justify-between items-center bg-card p-4 rounded-lg shadow-lg border border-gray-700">
        <div className="flex items-center gap-4">
          <Activity className="text-cyan-400" size={32} />
          <h1 className="text-2xl font-bold tracking-wider">AEROSPACE TELEMETRY // FUSION ENGINE</h1>
        </div>
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <span className={`w-3 h-3 rounded-full ${connected ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`}></span>
            <span className="text-sm text-gray-400">DATA LINK {connected ? 'ACTIVE' : 'OFFLINE'}</span>
          </div>
          <div className="bg-[#0b0f19] px-4 py-2 rounded flex gap-3 border border-gray-800">
            <span className="text-gray-400 flex items-center gap-1"><Thermometer size={16}/> T_amb:</span>
            <span className="font-mono text-amber-400">{latestTemp} °C</span>
          </div>
          <div className="bg-[#0b0f19] px-4 py-2 rounded flex gap-3 border border-gray-800">
            <span className="text-gray-400">Load:</span>
            <span className="font-mono text-emerald-400">{latestCurrent} A</span>
          </div>
          <div className={`px-4 py-2 rounded font-bold tracking-widest text-sm ${globalStatus === 'NOMINAL' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500' : 'bg-amber-500/20 text-amber-400 border border-amber-500'}`}>
            SYS: {globalStatus}
          </div>
        </div>
      </header>

      {/* Main Grid */}
      <main className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-grow">
        {/* Upper Left: Waveform (65% on lg screens approx 8 cols) */}
        <section className="lg:col-span-8 h-[360px]">
          <CurrentWaveform data={data} />
        </section>

        {/* Upper Right: Health Matrix (35% on lg screens approx 4 cols) */}
        <section className="lg:col-span-4 h-[360px]">
          <SensorHealthMatrix data={data} />
        </section>

        {/* Bottom Left: Bias Tracker */}
        <section className="lg:col-span-6 h-[320px]">
          <BiasTracker data={data} />
        </section>

        {/* Bottom Right: Fault Injector */}
        <section className="lg:col-span-6 h-[320px]">
          <FaultInjector />
        </section>
      </main>
    </div>
  );
}

export default App;
