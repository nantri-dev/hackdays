import type { TelemetryFrame, SensorData } from '../hooks/useTelemetry';

const SENSOR_NAMES = ['Shunt Resistor', 'Hall Sensor A', 'Hall Sensor B', 'Fluxgate Sensor'];

function TrustBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = value > 0.7 ? '#10b981' : value > 0.4 ? '#f59e0b' : '#e11d48';
  return (
    <div className="flex items-center gap-2 mt-1">
      <div className="flex-grow bg-gray-800 rounded-full h-1.5">
        <div
          className="h-1.5 rounded-full transition-all duration-300"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-[10px] font-mono" style={{ color }}>{pct}%</span>
    </div>
  );
}

export function SensorHealthMatrix({ data }: { data: TelemetryFrame[] }) {
  const current = data.length > 0 ? data[data.length - 1] : null;

  return (
    <div className="bg-card p-4 rounded-lg shadow-lg h-full border border-gray-700 overflow-auto">
      <h2 className="text-base font-semibold mb-3 text-cyan-400 font-mono tracking-wider">
        SENSOR HEALTH &amp; GATING
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {current && current.sensors.map((sensor: SensorData, idx: number) => {
          let badgeClass = 'bg-emerald-500/20 text-emerald-400 border border-emerald-500';
          if (sensor.status === 'DRIFTING')
            badgeClass = 'bg-amber-500/20 text-amber-400 border border-amber-500 animate-pulse';
          if (sensor.status === 'ISOLATED')
            badgeClass = 'bg-red-500/20 text-red-400 border border-red-500';

          const faultBadge = sensor.fault_class !== 'Healthy' ? sensor.fault_class : null;

          return (
            <div key={idx} className="bg-[#0b0f19] p-3 rounded border border-gray-800">
              <div className="flex justify-between items-center mb-1">
                <span className="font-medium text-xs text-gray-300">{SENSOR_NAMES[idx]}</span>
                <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold tracking-wider ${badgeClass}`}>
                  {sensor.status}
                </span>
              </div>

              {faultBadge && (
                <div className="text-[9px] mb-1 px-1.5 py-0.5 rounded bg-rose-900/40 text-rose-300 border border-rose-700 inline-block font-mono">
                  {faultBadge}
                </div>
              )}

              <div className="text-[10px] text-gray-400 grid grid-cols-2 gap-x-2 gap-y-0.5 mt-1">
                <span>Raw:</span>       <span className="text-right text-white font-mono">{sensor.raw.toFixed(2)} A</span>
                <span>Bias:</span>      <span className="text-right text-white font-mono">{sensor.bias.toFixed(3)} A</span>
                <span>Corrected:</span> <span className="text-right text-white font-mono">{sensor.corrected.toFixed(2)} A</span>
                <span>R-Factor:</span>  <span className="text-right text-white font-mono">×{sensor.r_factor.toFixed(1)}</span>
                <span>Fus. Wt:</span>   <span className="text-right text-cyan-400 font-mono">{(sensor.fusion_weight * 100).toFixed(1)}%</span>
              </div>

              <div className="mt-2">
                <span className="text-[9px] text-gray-500 font-mono">TRUST</span>
                <TrustBar value={sensor.trust_score} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
