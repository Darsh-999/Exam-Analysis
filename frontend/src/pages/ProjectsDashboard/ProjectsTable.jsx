import { useMemo, useState } from 'react';
import { ArrowUpDown } from 'lucide-react';
import DataTable from '../../components/DataTable';

const NUMERIC_COLUMNS = [
  { key: 'total_question_papers', header: 'Question Papers' },
  { key: 'total_syllabi', header: 'Syllabi' },
  { key: 'total_subjects', header: 'Subjects' },
  { key: 'total_questions', header: 'Questions' },
];

function formatDate(isoString) {
  return new Date(isoString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

// projects: rows already merged with their summary counts (see ProjectsDashboard)
export default function ProjectsTable({ projects, onRowClick }) {
  const [sortKey, setSortKey] = useState(null);
  const [sortDirection, setSortDirection] = useState('desc');

  // Default order (sortKey === null) is whatever the API returned, which is
  // already newest-first - only override it once the user clicks a header.
  const sortedProjects = useMemo(() => {
    if (!sortKey) return projects;
    const sorted = [...projects].sort((a, b) => a[sortKey] - b[sortKey]);
    return sortDirection === 'asc' ? sorted : sorted.reverse();
  }, [projects, sortKey, sortDirection]);

  function toggleSort(key) {
    if (sortKey === key) {
      setSortDirection((dir) => (dir === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDirection('desc');
    }
  }

  const columns = [
    {
      key: 'name',
      header: 'Project Name',
      render: (row) => <span className="font-semibold text-primary">{row.name}</span>,
    },
    {
      key: 'description',
      header: 'Description',
      render: (row) => (
        <span className="block max-w-[240px] truncate" title={row.description || ''}>
          {row.description || '—'}
        </span>
      ),
    },
    { key: 'created_by', header: 'Created By' },
    { key: 'created_at', header: 'Created On', render: (row) => formatDate(row.created_at) },
    ...NUMERIC_COLUMNS.map((col) => ({
      key: col.key,
      header: (
        <button
          type="button"
          onClick={() => toggleSort(col.key)}
          className="inline-flex items-center gap-1 hover:text-text-primary"
        >
          {col.header}
          <ArrowUpDown className="h-3 w-3" />
        </button>
      ),
      render: (row) => <span className="block text-right tabular-nums">{row[col.key]}</span>,
    })),
  ];

  return (
    <DataTable columns={columns} data={sortedProjects} keyField="id" onRowClick={onRowClick} />
  );
}
