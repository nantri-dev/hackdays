import type { TelemetryFrame, SensorData } from '../hooks/useTelemetry';

const sensorNames = ['Shunt Resistor', 'Hall Sensor A', 'Hall Sensor B', 'Fluxgate Sensor'];

export function SensorHealthMatrix({ data }: { data: TelemetryFrame[] }) {
  const current = data[data.length - 1] || null;

  return (
    <div className="bg-card p-4 rounded-lg shadow-lg h-full border border-gray-700">
      <h2 className="text-xl font-semibold mb-4 text-cyan-400">Sensor Health & Gating</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {current && current.sensors.map((sensor: SensorData, idx: number) => {
          let badgeClass = "bg-emerald-500/20 text-emerald-400 border border-emerald-500";
          if (sensor.status === 'DRIFTING') badgeClass = "bg-amber-500/20 text-amber-400 border border-amber-500 animate-pulse";
          if (sensor.status === 'ISOLATED') badgeClass = "bg-crimson-500/20 text-red-500 border border-red-600";

          return (
            <div key={idx} className="bg-[#0b0f19] p-3 rounded border border-gray-800">
              <div className="flex justify-between items-center mb-2">
                <span className="font-medium text-sm text-gray-300">{sensorNames[idx]}</span>
                <span className={`text-[10px] px-2 py-1 rounded font-bold tracking-wider ${badgeClass}`}>
                  {sensor.status}
                </span>
              </div>
              <div className="text-xs text-gray-400 grid grid-cols-2 gap-1 mt-2">
                <span>Raw:</span><span className="text-right text-white">{sensor.raw.toFixed(2)} A</span>
                <span>Bias:</span><span className="text-right text-white">{sensor.bias.toFixed(2)} A</span>
                <span>Corrected:</span><span className="text-right text-white">{sensor.corrected.toFixed(2)} A</span>
                <span>R-Factor:</span><span className="text-right text-white">x{sensor.r_factor.toFixed(1)}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
