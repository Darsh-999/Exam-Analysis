import DataTable from '../../components/DataTable';
import StatusBadge from '../../components/StatusBadge';

const STILL_PROCESSING = new Set(['extracting', 'classifying']);

// Numeric fields aren't meaningful until classification finishes, so show an
// em-dash instead of a misleading 0 while a paper is still processing.
function numericCell(row, key) {
  return STILL_PROCESSING.has(row.status) ? '—' : row[key];
}

const columns = [
  { key: 'filename', header: 'Document' },
  {
    key: 'status',
    header: 'Status',
    render: (row) => <StatusBadge status={row.status} />,
  },
  {
    key: 'subject',
    header: 'Subject',
    render: (row) =>
      row.subject_name ? `${row.subject_name} (${row.subject_code ?? '—'})` : '—',
  },
  {
    key: 'total_questions',
    header: 'Questions',
    render: (row) => numericCell(row, 'total_questions'),
  },
  {
    key: 'total_marks',
    header: 'Total Marks',
    render: (row) => numericCell(row, 'total_marks'),
  },
  {
    key: 'total_allocated_questions',
    header: 'Allocated',
    render: (row) => numericCell(row, 'total_allocated_questions'),
  },
  {
    key: 'total_unallocated_questions',
    header: 'Unallocated',
    render: (row) => numericCell(row, 'total_unallocated_questions'),
  },
  {
    key: 'total_multi_allocated_questions',
    header: 'Multi-allocated',
    render: (row) => numericCell(row, 'total_multi_allocated_questions'),
  },
];

// papers: QuestionPaperSummaryOut[] from GET /projects/:id/question-papers
export default function QuestionPapersTable({ papers }) {
  return <DataTable columns={columns} data={papers} keyField="id" />;
}
