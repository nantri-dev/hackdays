import { Flame, Magnet, AlertTriangle, RefreshCw } from 'lucide-react';

export function FaultInjector() {
  const injectFault = (type: string) => {
    console.log(`Injected: ${type}`);
    // In actual implementation, this sends a POST to /api/inject_fault
    fetch('/api/inject_fault', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fault_type: type })
    }).catch(e => console.warn("Backend not yet connected:", e));
  };

  return (
    <div className="bg-card p-4 rounded-lg shadow-lg h-full border border-gray-700">
      <h2 className="text-xl font-semibold mb-4 text-cyan-400">Mission Control: Stress Injection</h2>
      <div className="grid grid-cols-2 gap-3">
        <button 
          onClick={() => injectFault('heat_wave')}
          className="flex items-center gap-2 bg-amber-600 hover:bg-amber-500 text-white p-3 rounded transition-colors"
        >
          <Flame size={18} /> Heat Wave (+50°C Surge)
        </button>
        <button 
          onClick={() => injectFault('hall1_runaway')}
          className="flex items-center gap-2 bg-purple-600 hover:bg-purple-500 text-white p-3 rounded transition-colors"
        >
          <AlertTriangle size={18} /> Hall 1 Drift Runaway
        </button>
        <button 
          onClick={() => injectFault('hall2_saturation')}
          className="flex items-center gap-2 bg-orange-600 hover:bg-orange-500 text-white p-3 rounded transition-colors"
        >
          <Magnet size={18} /> Hall 2 Core Saturation
        </button>
        <button 
          onClick={() => injectFault('fluxgate_disconnect')}
          className="flex items-center gap-2 bg-red-600 hover:bg-red-500 text-white p-3 rounded transition-colors"
        >
          <AlertTriangle size={18} /> Fluxgate Disconnect
        </button>
      </div>
      <div className="mt-3">
        <button 
          onClick={() => injectFault('reset')}
          className="flex w-full justify-center items-center gap-2 bg-gray-700 hover:bg-gray-600 text-white p-3 rounded transition-colors"
        >
          <RefreshCw size={18} /> Reset Calibration & State
        </button>
      </div>
    </div>
  );
}
