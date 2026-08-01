import { FolderOpen } from 'lucide-react';
import AppShell from '../../components/AppShell';
import EmptyState from '../../components/EmptyState';

export default function ProjectsDashboard() {
  return (
    <AppShell breadcrumb={[{ label: 'Projects' }]}>
      <h1 className="text-2xl font-semibold text-text-primary">Projects</h1>
      <div className="mt-6 rounded-card bg-surface shadow-card">
        <EmptyState
          icon={FolderOpen}
          message="Project dashboard — built in Phase 4"
        />
      </div>
    </AppShell>
  );
}
