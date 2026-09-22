import type { GeminiDiagnostic } from '../hooks/useTelemetry';
import { Brain, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

const SENSOR_NAMES = ['Shunt Resistor', 'Hall Sensor A', 'Hall Sensor B', 'Fluxgate Sensor'];

const SEVERITY_STYLES: Record<string, string> = {
  Low:      'border-emerald-600 bg-emerald-950/40 text-emerald-400',
  Medium:   'border-amber-600 bg-amber-950/40 text-amber-400',
  High:     'border-orange-600 bg-orange-950/40 text-orange-400',
  Critical: 'border-red-600 bg-red-950/40 text-red-400',
};

const SEVERITY_ICON: Record<string, React.ReactNode> = {
  Low:      <CheckCircle size={14} className="text-emerald-400" />,
  Medium:   <AlertTriangle size={14} className="text-amber-400" />,
  High:     <AlertTriangle size={14} className="text-orange-400" />,
  Critical: <XCircle size={14} className="text-red-400" />,
};

export function DiagnosticBrief({ brief }: { brief: GeminiDiagnostic | null }) {
  if (!brief) {
    return (
      <div className="bg-card p-4 rounded-lg border border-gray-700 h-full flex flex-col">
        <h3 className="text-gray-400 font-mono text-xs tracking-widest mb-3 flex items-center gap-2">
          <Brain size={14} className="text-cyan-400" /> AI DIAGNOSTIC BRIEF
        </h3>
        <p className="text-gray-600 text-xs font-mono text-center mt-6">
          No fault event detected yet.
          <br />Inject a fault to trigger Gemini analysis.
        </p>
      </div>
    );
  }

  const sev = brief.severity ?? 'Low';
  const cardStyle = SEVERITY_STYLES[sev] ?? SEVERITY_STYLES.Low;
  const sensorName = SENSOR_NAMES[brief.sensor_id] ?? `Sensor ${brief.sensor_id}`;

  return (
    <div className="bg-card p-4 rounded-lg border border-gray-700 h-full flex flex-col overflow-auto">
      <h3 className="text-gray-400 font-mono text-xs tracking-widest mb-3 flex items-center gap-2">
        <Brain size={14} className="text-cyan-400" /> AI DIAGNOSTIC BRIEF
      </h3>

      <div className={`rounded-lg border p-3 flex flex-col gap-2 ${cardStyle}`}>
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {SEVERITY_ICON[sev]}
            <span className="font-mono text-xs font-bold">{sev.toUpperCase()} — {sensorName}</span>
          </div>
          <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-gray-800 text-gray-400">
            {brief.source === 'gemini' ? '⚡ GEMINI' : '⚠ FALLBACK'}
          </span>
        </div>

        {/* Diagnosis */}
        <p className="text-xs text-gray-200 leading-snug">{brief.diagnosis}</p>

        {/* Action */}
        <div className="border-t border-gray-700 pt-2">
          <span className="text-[9px] font-mono text-gray-500 uppercase">Action Required</span>
          <p className="text-xs text-gray-300 mt-0.5">{brief.action_required}</p>
        </div>

        {/* Confidence */}
        <div className="flex items-center gap-2">
          <span className="text-[9px] font-mono text-gray-500">Operator Confidence:</span>
          <div className="flex-grow bg-gray-800 rounded-full h-1.5">
            <div
              className="h-1.5 rounded-full bg-cyan-500"
              style={{ width: `${brief.operator_confidence}%` }}
            />
          </div>
          <span className="text-[10px] font-mono text-cyan-400">{brief.operator_confidence}%</span>
        </div>
      </div>
    </div>
  );
}
