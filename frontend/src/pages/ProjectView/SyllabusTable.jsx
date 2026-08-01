import { useNavigate } from 'react-router-dom';
import DataTable from '../../components/DataTable';
import StatusBadge from '../../components/StatusBadge';

const columns = [
  { key: 'filename', header: 'Document' },
  {
    key: 'status',
    header: 'Status',
    render: (row) => <StatusBadge status={row.status} errorMessage={row.error} />,
  },
  { key: 'total_topics', header: 'Topics' },
  { key: 'total_subtopics', header: 'Subtopics' },
];

// syllabi: SyllabusSummaryOut[] from GET /projects/:id/syllabi
// Clicking a row jumps to the Topics screen with that syllabus pre-selected.
export default function SyllabusTable({ projectId, syllabi }) {
  const navigate = useNavigate();

  return (
    <DataTable
      columns={columns}
      data={syllabi}
      keyField="id"
      onRowClick={(row) => navigate(`/projects/${projectId}/topics?syllabusId=${row.id}`)}
    />
  );
}
