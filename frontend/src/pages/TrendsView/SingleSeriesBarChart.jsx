import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import ChartPanel from './ChartPanel';
import { BRAND_COLOR } from './chartColors';

// Shared shape for Questions per Year and Mark Distribution: a plain
// single-color bar chart, one solid brand color per bar (§6.6 - color
// doesn't encode anything here, so no per-bar variation).
// chart: a ChartOut { title, description, x_label, y_label, data: [{label, value}] }
export default function SingleSeriesBarChart({ chart }) {
  return (
    <ChartPanel title={chart.title} description={chart.description}>
      <div style={{ height: 240 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chart.data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
            <XAxis dataKey="label" tick={{ fontSize: 12 }} stroke="var(--color-text-muted)" />
            <YAxis
              tick={{ fontSize: 12 }}
              stroke="var(--color-text-muted)"
              label={{ value: chart.y_label, angle: -90, position: 'insideLeft', fontSize: 12 }}
            />
            <Tooltip
              formatter={(value) => [value, chart.y_label]}
              contentStyle={{ fontSize: 12, borderRadius: 8, borderColor: 'var(--color-border)' }}
            />
            <Bar dataKey="value" fill={BRAND_COLOR} radius={[4, 4, 0, 0]} maxBarSize={56} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </ChartPanel>
  );
}
