import { useParams } from 'react-router-dom';
import { ListTree } from 'lucide-react';
import AppShell from '../../components/AppShell';
import EmptyState from '../../components/EmptyState';

export default function TopicsView() {
  const { projectId } = useParams();

  return (
    <AppShell
      breadcrumb={[
        { label: 'Projects', href: '/projects' },
        { label: projectId, href: `/projects/${projectId}` },
        { label: 'Topics' },
      ]}
    >
      <h1 className="text-2xl font-semibold text-text-primary">Topics</h1>
      <div className="mt-6 rounded-card bg-surface shadow-card">
        <EmptyState icon={ListTree} message="Topics / syllabus view — built in Phase 4" />
      </div>
    </AppShell>
  );
}
