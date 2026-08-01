import { useParams } from 'react-router-dom';
import { TrendingUp } from 'lucide-react';
import AppShell from '../../components/AppShell';
import EmptyState from '../../components/EmptyState';

export default function TrendsView() {
  const { projectId } = useParams();

  return (
    <AppShell
      breadcrumb={[
        { label: 'Projects', href: '/projects' },
        { label: projectId, href: `/projects/${projectId}` },
        { label: 'Trends' },
      ]}
    >
      <h1 className="text-2xl font-semibold text-text-primary">Trend & Insights</h1>
      <div className="mt-6 rounded-card bg-surface shadow-card">
        <EmptyState icon={TrendingUp} message="Trend & insights dashboard — built in Phase 4" />
      </div>
    </AppShell>
  );
}
