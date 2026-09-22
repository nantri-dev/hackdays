import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { TelemetryFrame } from '../hooks/useTelemetry';

export function BiasTracker({ data }: { data: TelemetryFrame[] }) {
  const chartData = data.map(d => ({
    time: new Date(d.timestamp).toLocaleTimeString(),
    b1: d.sensors[0].bias,
    b2: d.sensors[1].bias,
    b3: d.sensors[2].bias,
    b4: d.sensors[3].bias,
  }));

  return (
    <div className="bg-card p-4 rounded-lg shadow-lg h-full border border-gray-700">
      <h2 className="text-xl font-semibold mb-4 text-cyan-400">Dynamic Bias Estimation</h2>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
          <CartesianGrid stroke="#374151" strokeDasharray="3 3" />
          <XAxis dataKey="time" stroke="#9ca3af" tick={{fill: '#9ca3af'}} />
          <YAxis stroke="#9ca3af" tick={{fill: '#9ca3af'}} domain={[-1, 1]} />
          <Tooltip contentStyle={{ backgroundColor: '#151d30', borderColor: '#374151' }} />
          <Line type="monotone" dataKey="b1" stroke="#3b82f6" dot={false} strokeWidth={2} name="Shunt Bias" />
          <Line type="monotone" dataKey="b2" stroke="#8b5cf6" dot={false} strokeWidth={2} name="Hall 1 Bias" />
          <Line type="monotone" dataKey="b3" stroke="#f59e0b" dot={false} strokeWidth={2} name="Hall 2 Bias" />
          <Line type="monotone" dataKey="b4" stroke="#e11d48" dot={false} strokeWidth={2} name="Fluxgate Bias" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
