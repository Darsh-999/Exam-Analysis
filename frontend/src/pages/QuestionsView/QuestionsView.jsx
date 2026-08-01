import { useParams } from 'react-router-dom';
import { HelpCircle } from 'lucide-react';
import AppShell from '../../components/AppShell';
import EmptyState from '../../components/EmptyState';

export default function QuestionsView() {
  const { projectId } = useParams();

  return (
    <AppShell
      breadcrumb={[
        { label: 'Projects', href: '/projects' },
        { label: projectId, href: `/projects/${projectId}` },
        { label: 'Questions' },
      ]}
    >
      <h1 className="text-2xl font-semibold text-text-primary">Questions</h1>
      <div className="mt-6 rounded-card bg-surface shadow-card">
        <EmptyState icon={HelpCircle} message="Questions grid — built in Phase 4" />
      </div>
    </AppShell>
  );
}
