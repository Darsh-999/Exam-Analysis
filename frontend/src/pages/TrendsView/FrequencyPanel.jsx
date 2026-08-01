import { useCallback, useState } from 'react';
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { useApiData } from '../../hooks/useApiData';
import ChartPanel from './ChartPanel';
import MetricToggle from './MetricToggle';
import { createColorAssigner } from './chartColors';

const MAX_BARS = 12;

// fetcher: (projectId, metric) => Promise<ChartOut> - either
// trendsService.getTopicFrequency or getSubtopicFrequency.
// colorMap: pass the shared topic->color map for the Topics panel so it
// stays visually consistent with Marks per Paper; omit it for the
// Subtopics panel, which builds its own (subtopics don't reappear
// elsewhere on this page, so they don't need cross-chart consistency).
export default function FrequencyPanel({ projectId, fetcher, colorMap }) {
  const [metric, setMetric] = useState('count');

  const fetchChart = useCallback(() => fetcher(projectId, metric), [projectId, fetcher, metric]);
  const { data: chart, isLoading, error } = useApiData(fetchChart);

  const visible = chart ? chart.data.slice(0, MAX_BARS) : [];
  const hiddenCount = chart ? Math.max(0, chart.data.length - MAX_BARS) : 0;
  const getColor = colorMap ?? createColorAssigner(visible.map((d) => d.label));

  return (
    <div className="flex-1">
      {isLoading && <p className="text-sm text-text-muted">Loading…</p>}
      {error && <p className="text-sm text-critical">Couldn't load this chart: {error.message}</p>}

      {chart && (
        <ChartPanel
          title={chart.title}
          description={chart.description}
          toggle={<MetricToggle value={metric} onChange={setMetric} />}
        >
          <div style={{ height: Math.max(200, visible.length * 32) }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={visible}
                layout="vertical"
                margin={{ top: 4, right: 16, left: 8, bottom: 0 }}
              >
                <XAxis type="number" tick={{ fontSize: 12 }} stroke="var(--color-text-muted)" />
                <YAxis
                  type="category"
                  dataKey="label"
                  width={170}
                  tick={{ fontSize: 12 }}
                  stroke="var(--color-text-muted)"
                  // Some subtopic names run 80+ characters - recharts wraps
                  // long tick text onto multiple lines that overlap
                  // neighboring rows instead of truncating, so truncate it
                  // ourselves. The tooltip (hovering the bar) still shows
                  // the full name, since it reads from the raw data point.
                  tickFormatter={(label) => (label.length > 26 ? `${label.slice(0, 26)}…` : label)}
                />
                <Tooltip
                  formatter={(value) => [value, chart.x_label]}
                  contentStyle={{ fontSize: 12, borderRadius: 8, borderColor: 'var(--color-border)' }}
                />
                <Bar dataKey="value" radius={[0, 4, 4, 0]} maxBarSize={20}>
                  {visible.map((entry) => (
                    <Cell key={entry.label} fill={getColor(entry.label)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          {hiddenCount > 0 && (
            <p className="mt-2 text-xs text-text-muted">+{hiddenCount} more not shown</p>
          )}
        </ChartPanel>
      )}
    </div>
  );
}
