import { AlertTriangle, Zap, Thermometer, ShieldAlert } from 'lucide-react';
import { useState } from 'react';

export function FaultInjector() {
  const [loading, setLoading] = useState('');

  const injectFault = async (faultType: string) => {
    setLoading(faultType);
    try {
      await fetch('http://localhost:8000/api/inject_fault', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fault_type: faultType })
      });
    } catch (e) {
      console.error(e);
    }
    setLoading('');
  };

  return (
    <div className="bg-card rounded-lg border border-gray-700 h-full flex flex-col p-4 shadow-lg">
      <h3 className="text-gray-400 font-mono text-sm tracking-widest mb-4 flex items-center gap-2">
        <AlertTriangle size={16} className="text-amber-500"/> MISSION CONTROL: STRESS INJECTION
      </h3>
      
      <div className="grid grid-cols-2 gap-4 flex-grow">
        
        <button 
          onClick={() => injectFault('bias')}
          disabled={loading !== ''}
          className="bg-[#0b0f19] border border-gray-700 rounded p-4 flex flex-col items-center justify-center gap-2 hover:border-crimson-500 hover:text-crimson-400 transition-colors disabled:opacity-50"
        >
          <Thermometer size={24} />
          <span className="font-mono text-sm">BIAS DRIFT</span>
        </button>

        <button 
          onClick={() => injectFault('gain')}
          disabled={loading !== ''}
          className="bg-[#0b0f19] border border-gray-700 rounded p-4 flex flex-col items-center justify-center gap-2 hover:border-amber-500 hover:text-amber-400 transition-colors disabled:opacity-50"
        >
          <Zap size={24} />
          <span className="font-mono text-sm">GAIN DRIFT</span>
        </button>
        
        <button 
          onClick={() => injectFault('stuck')}
          disabled={loading !== ''}
          className="bg-[#0b0f19] border border-gray-700 rounded p-4 flex flex-col items-center justify-center gap-2 hover:border-crimson-500 hover:text-crimson-400 transition-colors disabled:opacity-50"
        >
          <ShieldAlert size={24} />
          <span className="font-mono text-sm">STUCK-AT</span>
        </button>

        <button 
          onClick={() => injectFault('noise')}
          disabled={loading !== ''}
          className="bg-[#0b0f19] border border-gray-700 rounded p-4 flex flex-col items-center justify-center gap-2 hover:border-amber-500 hover:text-amber-400 transition-colors disabled:opacity-50"
        >
          <Zap size={24} />
          <span className="font-mono text-sm">NOISE SPIKE</span>
        </button>

        <div className="col-span-2 grid grid-cols-2 gap-4 mt-2">
            <button 
            onClick={() => injectFault('network_offline')}
            disabled={loading !== ''}
            className="bg-crimson-900/20 border border-crimson-700 rounded p-2 flex flex-col items-center justify-center hover:bg-crimson-900 transition-colors disabled:opacity-50"
            >
            <span className="font-mono text-xs text-crimson-400">PULL CABLE (OFFLINE)</span>
            </button>
            <button 
            onClick={() => injectFault('network_online')}
            disabled={loading !== ''}
            className="bg-emerald-900/20 border border-emerald-700 rounded p-2 flex flex-col items-center justify-center hover:bg-emerald-900 transition-colors disabled:opacity-50"
            >
            <span className="font-mono text-xs text-emerald-400">RECONNECT CABLE (ONLINE)</span>
            </button>
        </div>

      </div>
      
      <button 
        onClick={() => injectFault('reset')}
        className="mt-4 bg-emerald-500/20 text-emerald-400 border border-emerald-500 rounded py-2 font-mono text-sm hover:bg-emerald-500 hover:text-white transition-colors"
      >
        SYS.RESET()
      </button>
    </div>
  );
}
