import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine,
} from 'recharts';
import type { TelemetryFrame } from '../hooks/useTelemetry';

const SENSOR_COLORS = ['#3b82f6', '#8b5cf6', '#f59e0b', '#e11d48'];
const SENSOR_LABELS = ['Shunt', 'Hall A', 'Hall B', 'Fluxgate'];

export function CurrentWaveform({ data }: { data: TelemetryFrame[] }) {
  const chartData = data.map(d => {
    const row: Record<string, number | string> = {
      time: new Date(d.timestamp).toLocaleTimeString(),
      true_current:  +d.true_current.toFixed(3),
      fused_current: +d.fused_current.toFixed(3),
      bound_hi: +d.bounds[1].toFixed(3),
      bound_lo: +d.bounds[0].toFixed(3),
    };
    d.sensors.forEach((s, i) => {
      row[`s${i}`] = +s.raw.toFixed(3);
    });
    return row;
  });

  // Compute a tight but padded domain from the visible data
  let minY = Infinity, maxY = -Infinity;
  chartData.forEach(row => {
    ['true_current', 'fused_current', 'bound_hi', 'bound_lo', 's0', 's1', 's2', 's3'].forEach(k => {
      const v = row[k] as number;
      if (isFinite(v) && Math.abs(v) < 1000) {
        if (v < minY) minY = v;
        if (v > maxY) maxY = v;
      }
    });
  });
  if (!isFinite(minY)) { minY = -5; maxY = 30; }
  const pad = Math.max((maxY - minY) * 0.15, 2);
  const domain: [number, number] = [
    Math.round((minY - pad) * 10) / 10,
    Math.round((maxY + pad) * 10) / 10,
  ];

  return (
    <div className="bg-card p-4 rounded-lg shadow-lg h-full border border-gray-700 flex flex-col">
      <h2 className="text-base font-semibold mb-3 text-cyan-400 font-mono tracking-wider">
        HIGH-FREQUENCY WAVEFORM
      </h2>

      {/* Legend */}
      <div className="flex gap-4 mb-2 flex-wrap">
        <span className="flex items-center gap-1 text-xs text-gray-400 font-mono">
          <span className="inline-block w-6 h-0.5 bg-white opacity-80" style={{border:'1px dashed white'}}/> True Current
        </span>
        <span className="flex items-center gap-1 text-xs text-gray-400 font-mono">
          <span className="inline-block w-6 h-0.5 bg-emerald-400"/> Fused (UKF)
        </span>
        {SENSOR_LABELS.map((l, i) => (
          <span key={i} className="flex items-center gap-1 text-xs text-gray-400 font-mono">
            <span className="inline-block w-6 h-0.5" style={{backgroundColor: SENSOR_COLORS[i], opacity: 0.7}}/> {l}
          </span>
        ))}
      </div>

      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 5, right: 16, bottom: 5, left: 4 }}>
          <CartesianGrid stroke="#1f2937" strokeDasharray="3 3" />
          <XAxis
            dataKey="time"
            stroke="#4b5563"
            tick={{ fill: '#6b7280', fontSize: 10 }}
            interval="preserveStartEnd"
          />
          <YAxis
            stroke="#4b5563"
            tick={{ fill: '#6b7280', fontSize: 10 }}
            domain={domain}
            width={46}
          />
          <Tooltip
            contentStyle={{ backgroundColor: '#0b0f19', borderColor: '#374151', fontSize: 11 }}
            itemStyle={{ color: '#d1d5db' }}
          />
          <ReferenceLine y={0} stroke="#374151" strokeDasharray="2 4" />

          {/* Confidence band — draw as two separate faint lines, NOT area */}
          <Line type="monotone" dataKey="bound_hi" stroke="#10b981" strokeWidth={1}
            strokeOpacity={0.3} dot={false} isAnimationActive={false} name="Upper bound" />
          <Line type="monotone" dataKey="bound_lo" stroke="#10b981" strokeWidth={1}
            strokeOpacity={0.3} dot={false} isAnimationActive={false} name="Lower bound" />

          {/* Raw sensor readings */}
          {[0, 1, 2, 3].map(i => (
            <Line key={i} type="monotone" dataKey={`s${i}`}
              stroke={SENSOR_COLORS[i]} strokeWidth={1.5} strokeOpacity={0.55}
              dot={false} isAnimationActive={false} name={SENSOR_LABELS[i]} />
          ))}

          {/* True current — dashed white, drawn ON TOP */}
          <Line type="monotone" dataKey="true_current"
            stroke="#ffffff" strokeWidth={2.5} strokeDasharray="6 3"
            dot={false} isAnimationActive={false} name="True Current" />

          {/* Fused estimate — bold green */}
          <Line type="monotone" dataKey="fused_current"
            stroke="#10b981" strokeWidth={3}
            dot={false} isAnimationActive={false} name="Fused (UKF)" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
