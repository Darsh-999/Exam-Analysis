import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import ChartPanel from './ChartPanel';
import { STATUS_COLORS } from './chartColors';

const BAR_WIDTH_PX = 56;

const RAW_KEY_BY_NAME = {
  'Single-allocated': 'single_allocated',
  'Multi-allocated': 'multi_allocated',
  Unallocated: 'unallocated',
};

// chart: an AllocationHealthOut. Rendered as a 100%-stacked bar (counts
// converted to percent-of-paper) using the reserved status palette - this is
// a "is the data trustworthy" signal, not a content chart, so it
// intentionally does NOT reuse the topic color palette (§6.4).
export default function AllocationHealthChart({ chart }) {
  const rows = chart.data.map((entry) => {
    const total = entry.total_questions || 1;
    return {
      label: entry.filename,
      single_allocated: (entry.single_allocated / total) * 100,
      multi_allocated: (entry.multi_allocated / total) * 100,
      unallocated: (entry.unallocated / total) * 100,
      raw: entry,
    };
  });

  return (
    <ChartPanel title={chart.title} description={chart.description}>
      <p className="mb-3 text-xs text-text-muted">
        Green = single-allocated (good) · Amber = multi-allocated (informational, not an error) ·
        Red = unallocated (worth reviewing)
      </p>
      <div className="overflow-x-auto">
        <div style={{ height: 320, minWidth: rows.length * BAR_WIDTH_PX }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={rows} margin={{ top: 4, right: 16, left: 0, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
              <XAxis
                dataKey="label"
                tick={{ fontSize: 11 }}
                stroke="var(--color-text-muted)"
                interval={0}
                angle={-30}
                textAnchor="end"
                height={70}
              />
              <YAxis
                tick={{ fontSize: 12 }}
                stroke="var(--color-text-muted)"
                tickFormatter={(value) => `${value}%`}
              />
              <Tooltip
                formatter={(value, name, props) => [
                  `${props.payload.raw[RAW_KEY_BY_NAME[name]]} questions`,
                  name,
                ]}
                contentStyle={{ fontSize: 12, borderRadius: 8, borderColor: 'var(--color-border)' }}
              />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar dataKey="single_allocated" stackId="alloc" name="Single-allocated" fill={STATUS_COLORS.singleAllocated} />
              <Bar dataKey="multi_allocated" stackId="alloc" name="Multi-allocated" fill={STATUS_COLORS.multiAllocated} />
              <Bar dataKey="unallocated" stackId="alloc" name="Unallocated" fill={STATUS_COLORS.unallocated} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </ChartPanel>
  );
}
