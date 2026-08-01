import { useMemo, useState } from 'react';
import ChartPanel from './ChartPanel';
import { heatmapColorFor } from './chartColors';

const DEFAULT_VISIBLE_ROWS = 15;

// chart: a HeatmapOut { rows (topics, most-tested first), columns (years,
// chronological), data: [{row, column, value}] }
export default function TopicYearHeatmap({ chart }) {
  const [showAll, setShowAll] = useState(false);

  const cellValue = useMemo(() => {
    const map = new Map();
    for (const cell of chart.data) map.set(`${cell.row}|${cell.column}`, cell.value);
    return map;
  }, [chart.data]);

  // A (topic, year) pair missing from the API response is a real zero, not
  // a gap - cellValue.get(...) below already defaults to 0 for that case.
  const maxValue = useMemo(
    () => chart.data.reduce((max, cell) => Math.max(max, cell.value), 0) || 1,
    [chart.data]
  );

  const visibleRows = showAll ? chart.rows : chart.rows.slice(0, DEFAULT_VISIBLE_ROWS);
  const hiddenRowCount = chart.rows.length - visibleRows.length;

  return (
    <ChartPanel title={chart.title} description={chart.description}>
      <div className="overflow-x-auto rounded-btn border border-border">
        <table className="border-collapse text-xs">
          <thead>
            <tr>
              <th className="sticky left-0 z-10 bg-surface px-2 py-1.5" />
              {chart.columns.map((year) => (
                <th key={year} className="px-2 py-1.5 text-center font-medium text-text-secondary">
                  {year}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visibleRows.map((topic) => (
              <tr key={topic}>
                <th
                  title={topic}
                  className="sticky left-0 z-10 max-w-[220px] truncate bg-surface px-2 py-1.5 text-left font-medium text-text-secondary"
                >
                  {topic}
                </th>
                {chart.columns.map((year) => {
                  const value = cellValue.get(`${topic}|${year}`) ?? 0;
                  const fraction = value / maxValue;
                  return (
                    <td
                      key={year}
                      title={`${topic} · ${year}: ${value} question${value === 1 ? '' : 's'}`}
                      className={`h-8 w-10 border border-surface text-center ${
                        fraction > 0.5 ? 'text-white' : 'text-text-primary'
                      }`}
                      style={{ backgroundColor: heatmapColorFor(fraction) }}
                    >
                      {value > 0 ? value : ''}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {chart.rows.length > DEFAULT_VISIBLE_ROWS && (
        <button
          type="button"
          onClick={() => setShowAll((prev) => !prev)}
          className="mt-3 text-xs font-medium text-primary hover:underline"
        >
          {showAll ? 'Show fewer topics' : `Show all ${chart.rows.length} topics (${hiddenRowCount} more)`}
        </button>
      )}
    </ChartPanel>
  );
}
