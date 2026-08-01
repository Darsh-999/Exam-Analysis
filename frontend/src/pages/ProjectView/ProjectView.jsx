import { useParams } from 'react-router-dom';
import { FileText } from 'lucide-react';
import AppShell from '../../components/AppShell';
import EmptyState from '../../components/EmptyState';

export default function ProjectView() {
  const { projectId } = useParams();

  return (
    <AppShell
      breadcrumb={[{ label: 'Projects', href: '/projects' }, { label: projectId }]}
    >
      <h1 className="text-2xl font-semibold text-text-primary">
        Project {projectId}
      </h1>
      <div className="mt-6 rounded-card bg-surface shadow-card">
        <EmptyState icon={FileText} message="Project view — built in Phase 4" />
      </div>
    </AppShell>
  );
}
