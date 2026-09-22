import { Activity } from 'lucide-react';
import { CurrentWaveform } from './components/CurrentWaveform';
import { SensorHealthMatrix } from './components/SensorHealthMatrix';
import { FaultInjector } from './components/FaultInjector';
import { BiasTracker } from './components/BiasTracker';
import { NetworkStatus } from './components/NetworkStatus';
import { EventLog } from './components/EventLog';
import { useTelemetry } from './hooks/useTelemetry';

function App() {
  const { data, connected, globalStatus } = useTelemetry();

  return (
    <div className="min-h-screen bg-background text-white p-6 font-sans flex flex-col gap-6">
      <header className="flex justify-between items-center bg-card p-4 rounded-lg shadow-lg border border-gray-700">
        <div className="flex items-center gap-4">
          <Activity className="text-cyan-400" size={32} />
          <h1 className="text-2xl font-bold tracking-wider">AEROSPACE TELEMETRY // FUSION ENGINE</h1>
        </div>
        <div className="flex items-center gap-6">
          <NetworkStatus data={data} />
          <div className="flex items-center gap-2 bg-[#0b0f19] px-4 py-2 rounded-full border border-gray-800">
            <span className={`w-3 h-3 rounded-full ${connected ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`}></span>
            <span className="text-sm font-mono text-gray-400">DATA LINK {connected ? 'ACTIVE' : 'OFFLINE'}</span>
          </div>
          <div className={`px-4 py-2 rounded font-bold tracking-widest text-sm ${globalStatus === 'NOMINAL' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500' : 'bg-amber-500/20 text-amber-400 border border-amber-500'}`}>
            SYS: {globalStatus}
          </div>
        </div>
      </header>

      <main className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-grow">
        {/* Left Column (8 cols) */}
        <section className="lg:col-span-8 flex flex-col gap-6">
          <div className="h-[360px]">
            <CurrentWaveform data={data} />
          </div>
          <div className="h-[300px]">
            <BiasTracker data={data} />
          </div>
        </section>

        {/* Right Column (4 cols) */}
        <section className="lg:col-span-4 flex flex-col gap-6">
          <div className="h-[200px]">
            <SensorHealthMatrix data={data} globalStatus={globalStatus} />
          </div>
          <div className="h-[200px]">
            <FaultInjector />
          </div>
          <div className="h-[240px]">
            <EventLog data={data} />
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
