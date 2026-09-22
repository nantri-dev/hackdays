import { Wifi, WifiOff, Database } from 'lucide-react';
import type { TelemetryFrame } from '../hooks/useTelemetry';

export function NetworkStatus({ data }: { data: TelemetryFrame[] }) {
  if (data.length === 0) return null;
  const latest = data[data.length - 1];
  const isOnline = latest.is_online ?? true;
  const queueSize = latest.queue_size ?? 0;

  return (
    <div className="flex items-center gap-4">
      <div className="flex items-center gap-2">
        {isOnline ? (
          <span className="flex items-center gap-1 text-emerald-400 font-mono text-sm">
            <Wifi size={16} className="animate-pulse" /> ONLINE
          </span>
        ) : (
          <span className="flex items-center gap-1 text-rose-400 font-mono text-sm">
            <WifiOff size={16} /> OFFLINE
          </span>
        )}
      </div>
      <div className={`flex items-center gap-1 font-mono text-sm ${queueSize > 0 ? 'text-amber-400' : 'text-gray-500'}`}>
        <Database size={14} />
        <span>QUEUE: {queueSize}</span>
      </div>
    </div>
  );
}
