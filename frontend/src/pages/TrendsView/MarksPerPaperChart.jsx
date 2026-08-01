import { useMemo } from 'react';
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import ChartPanel from './ChartPanel';
import { OTHER_COLOR, OTHER_LABEL } from './chartColors';

const BAR_WIDTH_PX = 64;

// chart: a MarksPerPaperOut. topicColorMap: the shared label->color lookup
// built in TrendsView, reused here so a topic is the same color everywhere
// it appears on the page (§6.3).
export default function MarksPerPaperChart({ chart, topicColorMap }) {
  // Only the shared map's top-8 topics get their own stacked series + legend
  // entry - everything else is summed into one "Other" series per bar, so a
  // project with dozens of topics doesn't produce a legend with dozens of
  // redundant gray entries (§6.6: beyond 8, fold into one Other bucket).
  const knownTopics = useMemo(() => {
    const seen = new Set();
    for (const entry of chart.data) {
      for (const segment of entry.segments) {
        if (topicColorMap.isKnown(segment.topic)) seen.add(segment.topic);
      }
    }
    return Array.from(seen);
  }, [chart.data, topicColorMap]);

  const rows = useMemo(
    () =>
      chart.data.map((entry) => {
        const row = {
          label:
            entry.subject_code && entry.exam_date
              ? `${entry.subject_code} (${entry.exam_date})`
              : entry.filename,
          total_marks: entry.total_marks,
        };
        let otherMarks = 0;
        for (const segment of entry.segments) {
          if (topicColorMap.isKnown(segment.topic)) {
            row[segment.topic] = segment.marks;
          } else {
            otherMarks += segment.marks;
          }
        }
        row[OTHER_LABEL] = otherMarks;
        return row;
      }),
    [chart.data, topicColorMap]
  );

  const hasOtherTopics = rows.some((row) => row[OTHER_LABEL] > 0);

  return (
    <ChartPanel title={chart.title} description={chart.description}>
      <div className="overflow-x-auto">
        <div style={{ height: 380, minWidth: rows.length * BAR_WIDTH_PX }}>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={rows} margin={{ top: 4, right: 16, left: 0, bottom: 8 }}>
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
              <YAxis tick={{ fontSize: 12 }} stroke="var(--color-text-muted)" />
              <Tooltip
                contentStyle={{ fontSize: 12, borderRadius: 8, borderColor: 'var(--color-border)' }}
              />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              {knownTopics.map((topic) => (
                <Bar key={topic} dataKey={topic} stackId="marks" fill={topicColorMap(topic)} />
              ))}
              {hasOtherTopics && (
                <Bar dataKey={OTHER_LABEL} stackId="marks" fill={OTHER_COLOR} />
              )}
              <Line
                type="monotone"
                dataKey="total_marks"
                name="Total Marks"
                stroke="var(--color-nav)"
                strokeWidth={2}
                dot={{ r: 3 }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>
    </ChartPanel>
  );
}
