import { MessageSquare, Clock } from 'lucide-react';
import type { TelemetryFrame } from '../hooks/useTelemetry';

export function EventLog({ data }: { data: TelemetryFrame[] }) {
  const latest = data.length > 0 ? data[data.length - 1] : null;
  const events = latest?.events ?? [];

  return (
    <div className="bg-card p-4 rounded-lg shadow-lg border border-gray-700 h-full overflow-hidden flex flex-col">
      <h3 className="text-gray-400 font-mono text-xs tracking-widest mb-3 flex items-center gap-2">
        <MessageSquare size={14} className="text-cyan-400" /> AI EVENT LOG
      </h3>

      <div className="flex flex-col gap-2 overflow-y-auto flex-grow">
        {events.length === 0 ? (
          <p className="text-gray-600 text-xs font-mono text-center mt-6">
            No events logged yet. Inject a fault to see analysis.
          </p>
        ) : (
          events.map((ev, i) => (
            <div
              key={i}
              className={`p-2 rounded border text-xs ${
                ev.is_fallback
                  ? 'bg-amber-900/20 border-amber-700/50'
                  : 'bg-cyan-900/20 border-cyan-700/50'
              }`}
            >
              <div className="flex justify-between items-center mb-1">
                <span
                  className={`font-mono font-bold px-1 py-0.5 rounded ${
                    ev.is_fallback
                      ? 'bg-amber-500/20 text-amber-400'
                      : 'bg-cyan-500/20 text-cyan-400'
                  }`}
                >
                  {ev.is_fallback ? 'PENDING SYNC' : 'GEMINI ANALYSIS'}
                </span>
                <span className="text-gray-500 flex items-center gap-1 font-mono">
                  <Clock size={10} />
                  {new Date(ev.timestamp * 1000).toLocaleTimeString()}
                </span>
              </div>
              <p className="text-gray-300 leading-snug">{ev.message}</p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
