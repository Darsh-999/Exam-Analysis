import { useCallback, useMemo, useState } from 'react';
import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';
import { useApiData } from '../../hooks/useApiData';
import { getQuestionPaperTopicDistribution } from '../../services/questionPapersService';
import ChartPanel from './ChartPanel';
import { OTHER_COLOR, OTHER_LABEL } from './chartColors';

const selectClasses =
  'h-9 rounded-btn border border-border bg-surface px-3 text-sm text-text-primary focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20';

// papers: QuestionPaperSummaryOut[], already most-recently-uploaded-first
// from the API - that ordering is exactly the spec's default selection.
// topicColorMap: the shared label->color lookup, so a topic's slice here
// matches its color in the Topic Frequency / Marks per Paper charts.
export default function TopicDistributionChart({ papers, topicColorMap }) {
  const [selectedPaperId, setSelectedPaperId] = useState(papers[0]?.id ?? null);

  const fetchChart = useCallback(() => {
    return selectedPaperId
      ? getQuestionPaperTopicDistribution(selectedPaperId)
      : Promise.resolve(null);
  }, [selectedPaperId]);
  const { data: chart, isLoading, error } = useApiData(fetchChart);

  // "Unallocated" always stays its own distinct wedge (explicit in the spec
  // - it's a coverage signal, not noise to hide). Every other topic beyond
  // the shared map's top 8 gets merged into one "Other" wedge instead of
  // each keeping its own same-colored-but-separate slice + legend entry.
  const coloredData = useMemo(() => {
    if (!chart) return [];
    const result = [];
    let otherTotal = 0;
    for (const point of chart.data) {
      if (point.label === 'Unallocated') {
        result.push({ ...point, color: OTHER_COLOR });
      } else if (topicColorMap.isKnown(point.label)) {
        result.push({ ...point, color: topicColorMap(point.label) });
      } else {
        otherTotal += point.value;
      }
    }
    if (otherTotal > 0) {
      result.push({ label: OTHER_LABEL, value: otherTotal, color: OTHER_COLOR });
    }
    return result;
  }, [chart, topicColorMap]);

  return (
    <div>
      <select
        value={selectedPaperId ?? ''}
        onChange={(e) => setSelectedPaperId(e.target.value)}
        className={`mb-4 ${selectClasses}`}
      >
        {papers.map((paper) => (
          <option key={paper.id} value={paper.id}>
            {paper.filename}
            {paper.subject_code ? ` (${paper.subject_code})` : ''}
          </option>
        ))}
      </select>

      {isLoading && <p className="text-sm text-text-muted">Loading…</p>}
      {error && <p className="text-sm text-critical">Couldn't load this chart: {error.message}</p>}

      {chart && (
        <ChartPanel title={chart.title} description={chart.description}>
          <div style={{ height: 320 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={coloredData} dataKey="value" nameKey="label" innerRadius={60} outerRadius={110} paddingAngle={1}>
                  {coloredData.map((entry) => (
                    <Cell key={entry.label} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value, name) => [value, name]}
                  contentStyle={{ fontSize: 12, borderRadius: 8, borderColor: 'var(--color-border)' }}
                />
                <Legend wrapperStyle={{ fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </ChartPanel>
      )}
    </div>
  );
}
