// columns: [{ key, header, render?(row) }]
// data: array of row objects
// onRowClick: optional (row) => void — makes rows clickable when provided
export default function DataTable({ columns, data, keyField = 'id', onRowClick }) {
  return (
    <div className="overflow-x-auto rounded-card bg-surface shadow-card">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="bg-background">
            {columns.map((col) => (
              <th
                key={col.key}
                className="border-b border-border px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-text-secondary"
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr
              key={row[keyField]}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
              className={`h-14 border-b border-border last:border-0 ${
                onRowClick ? 'cursor-pointer hover:bg-background' : ''
              }`}
            >
              {columns.map((col) => (
                <td key={col.key} className="px-4 py-3 text-text-primary">
                  {col.render ? col.render(row) : row[col.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
