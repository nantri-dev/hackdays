import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
} from 'recharts';
import type { TelemetryFrame } from '../hooks/useTelemetry';

const SENSOR_COLORS = ['#3b82f6', '#8b5cf6', '#f59e0b', '#e11d48'];
const SENSOR_LABELS = ['Shunt', 'Hall A', 'Hall B', 'Fluxgate'];

export function BiasTracker({ data }: { data: TelemetryFrame[] }) {
  const chartData = data.map(d => {
    const row: Record<string, number | string> = {
      time: new Date(d.timestamp).toLocaleTimeString(),
    };
    d.sensors.forEach((s, i) => {
      // Clamp to sane range to avoid chart blow-up from diverged UKF
      const b = s.bias;
      row[`b${i}`] = isFinite(b) && Math.abs(b) < 200 ? +b.toFixed(4) : null as any;
    });
    return row;
  });

  return (
    <div className="bg-card p-4 rounded-lg shadow-lg h-full border border-gray-700 flex flex-col">
      <h2 className="text-base font-semibold mb-3 text-cyan-400 font-mono tracking-wider">
        DYNAMIC BIAS ESTIMATION
      </h2>

      <div className="flex gap-4 mb-2 flex-wrap">
        {SENSOR_LABELS.map((l, i) => (
          <span key={i} className="flex items-center gap-1 text-xs text-gray-400 font-mono">
            <span className="inline-block w-5 h-0.5" style={{backgroundColor: SENSOR_COLORS[i]}}/> {l}
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
            domain={['auto', 'auto']}
            width={46}
          />
          <Tooltip
            contentStyle={{ backgroundColor: '#0b0f19', borderColor: '#374151', fontSize: 11 }}
            itemStyle={{ color: '#d1d5db' }}
          />
          {[0, 1, 2, 3].map(i => (
            <Line key={i} type="monotone" dataKey={`b${i}`}
              stroke={SENSOR_COLORS[i]} strokeWidth={2}
              dot={false} isAnimationActive={false}
              connectNulls={false} name={`${SENSOR_LABELS[i]} Bias`} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
