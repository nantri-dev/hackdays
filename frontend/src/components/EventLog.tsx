import { MessageSquare, Clock } from 'lucide-react';
import type { TelemetryFrame } from '../hooks/useTelemetry';

export function EventLog({ data }: { data: TelemetryFrame[] }) {
  if (data.length === 0) return null;
  const latest = data[data.length - 1];
  
  return (
    <div className="bg-card p-4 rounded-lg shadow-lg border border-gray-700 h-full overflow-hidden flex flex-col">
      <h3 className="text-gray-400 font-mono text-sm tracking-widest mb-4 flex items-center gap-2">
        <MessageSquare size={16} className="text-cyan-400"/> AI EVENT LOG
      </h3>
      
      <div className="flex flex-col gap-3 overflow-y-auto pr-2 flex-grow">
        {latest.events.map((ev, i) => (
          <div key={i} className={`p-3 rounded border ${ev.is_fallback ? 'bg-amber-900/20 border-amber-700/50' : 'bg-cyan-900/20 border-cyan-700/50'}`}>
            <div className="flex justify-between items-center mb-2">
              <span className={`font-mono text-xs font-bold px-2 py-1 rounded ${ev.is_fallback ? 'bg-amber-500/20 text-amber-400' : 'bg-cyan-500/20 text-cyan-400'}`}>
                {ev.is_fallback ? 'PENDING SYNC' : 'GEMINI ANALYSIS'}
              </span>
              <span className="text-gray-500 text-xs flex items-center gap-1 font-mono">
                <Clock size={12}/> {new Date(ev.timestamp * 1000).toLocaleTimeString()}
              </span>
            </div>
            <p className="text-sm text-gray-300 font-sans leading-relaxed">
              {ev.message}
            </p>
          </div>
        ))}
        {latest.events.length === 0 && (
          <div className="text-gray-500 text-sm font-mono text-center mt-10">No events logged yet.</div>
        )}
      </div>
    </div>
  );
}
