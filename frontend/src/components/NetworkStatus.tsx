import { Wifi, WifiOff, Database } from 'lucide-react';
import type { TelemetryFrame } from '../hooks/useTelemetry';

export function NetworkStatus({ data }: { data: TelemetryFrame[] }) {
  if (data.length === 0) return null;
  const latest = data[data.length - 1];
  
  return (
    <div className="bg-card p-4 rounded-lg shadow-lg border border-gray-700 flex justify-between items-center">
      <div className="flex items-center gap-3">
        {latest.is_online ? (
          <div className="flex items-center gap-2 text-emerald-400 font-mono">
            <Wifi size={20} className="animate-pulse" />
            <span>ONLINE</span>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-crimson-500 font-mono">
            <WifiOff size={20} />
            <span>OFFLINE (SIMULATED)</span>
          </div>
        )}
      </div>
      
      <div className={`flex items-center gap-2 font-mono ${latest.queue_size > 0 ? 'text-amber-400' : 'text-gray-400'}`}>
        <Database size={16} />
        <span>LOCAL QUEUE: {latest.queue_size} EVENTS</span>
      </div>
    </div>
  );
}
