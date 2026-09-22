import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Area, AreaChart, ResponsiveContainer, ComposedChart } from 'recharts';
import type { TelemetryFrame } from '../hooks/useTelemetry';

export function CurrentWaveform({ data }: { data: TelemetryFrame[] }) {
  const chartData = data.map(d => ({
    time: new Date(d.timestamp).toLocaleTimeString(),
    true_current: d.true_current,
    fused_current: d.fused_current,
    lower: d.bounds[0],
    upper: d.bounds[1],
    s1: d.sensors[0].raw,
    s2: d.sensors[1].raw,
    s3: d.sensors[2].raw,
    s4: d.sensors[3].raw,
  }));

  return (
    <div className="bg-card p-4 rounded-lg shadow-lg h-full border border-gray-700">
      <h2 className="text-xl font-semibold mb-4 text-cyan text-cyan-400">High-Frequency Waveform Chart</h2>
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
          <CartesianGrid stroke="#374151" strokeDasharray="3 3" />
          <XAxis dataKey="time" stroke="#9ca3af" tick={{fill: '#9ca3af'}} />
          <YAxis stroke="#9ca3af" tick={{fill: '#9ca3af'}} domain={['auto', 'auto']} />
          <Tooltip contentStyle={{ backgroundColor: '#151d30', borderColor: '#374151' }} />
          
          <Area type="monotone" dataKey="upper" stroke="none" fill="#10b981" fillOpacity={0.1} />
          <Area type="monotone" dataKey="lower" stroke="none" fill="#0b0f19" fillOpacity={1} />
          
          <Line type="monotone" dataKey="true_current" stroke="#ffffff" strokeDasharray="5 5" dot={false} strokeWidth={2} name="True Current" />
          <Line type="monotone" dataKey="fused_current" stroke="#10b981" dot={false} strokeWidth={2} name="Fused Estimate" />
          
          <Line type="monotone" dataKey="s1" stroke="#3b82f6" dot={false} strokeWidth={1} strokeOpacity={0.5} name="Shunt" />
          <Line type="monotone" dataKey="s2" stroke="#8b5cf6" dot={false} strokeWidth={1} strokeOpacity={0.5} name="Hall 1" />
          <Line type="monotone" dataKey="s3" stroke="#f59e0b" dot={false} strokeWidth={1} strokeOpacity={0.5} name="Hall 2" />
          <Line type="monotone" dataKey="s4" stroke="#e11d48" dot={false} strokeWidth={1} strokeOpacity={0.5} name="Fluxgate" />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
