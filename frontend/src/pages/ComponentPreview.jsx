import { useState } from 'react';
import { FileText, FolderOpen } from 'lucide-react';
import TopNav from '../components/TopNav';
import StatCard from '../components/StatCard';
import StatusBadge from '../components/StatusBadge';
import Button from '../components/Button';
import DataTable from '../components/DataTable';
import Modal from '../components/Modal';
import EmptyState from '../components/EmptyState';

// THROWAWAY page — only exists to eyeball Phase 1 components together.
// Delete this file (and its temporary route/import) once Phase 1 is signed off.
const SAMPLE_ROWS = [
  { id: 1, name: 'Midterm 2023.pdf', status: 'completed' },
  { id: 2, name: 'Final 2024.pdf', status: 'extracting' },
  { id: 3, name: 'Quiz 1.pdf', status: 'failed' },
];

export default function ComponentPreview() {
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <div className="min-h-screen bg-background">
      <TopNav
        breadcrumb={[
          { label: 'Projects', href: '/projects' },
          { label: 'Data Structures 2024' },
        ]}
        userEmail="drocks12226@gmail.com"
        onLogout={() => alert('logout clicked')}
      />

      <main className="mx-auto max-w-[1280px] space-y-10 px-6 py-10">
        <section>
          <h2 className="mb-4 text-lg font-semibold">Buttons</h2>
          <div className="flex flex-wrap items-center gap-3">
            <Button>Primary</Button>
            <Button variant="secondary">Secondary</Button>
            <Button size="sm">Primary sm</Button>
            <Button variant="secondary" size="sm">
              Secondary sm
            </Button>
            <Button disabled>Disabled</Button>
          </div>
        </section>

        <section>
          <h2 className="mb-4 text-lg font-semibold">Stat cards</h2>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
            <StatCard label="Total Papers" value="24" icon={FileText} />
            <StatCard label="Active Projects" value="5" icon={FolderOpen} />
            <StatCard label="Questions" value="1,204" />
          </div>
        </section>

        <section>
          <h2 className="mb-4 text-lg font-semibold">Status badges</h2>
          <div className="flex flex-wrap gap-3">
            <StatusBadge status="extracting" />
            <StatusBadge status="classifying" />
            <StatusBadge status="completed" />
            <StatusBadge status="failed" errorMessage="OCR failed: unreadable scan" />
          </div>
        </section>

        <section>
          <h2 className="mb-4 text-lg font-semibold">Data table</h2>
          <DataTable
            columns={[
              { key: 'name', header: 'File name' },
              {
                key: 'status',
                header: 'Status',
                render: (row) => <StatusBadge status={row.status} />,
              },
            ]}
            data={SAMPLE_ROWS}
            onRowClick={(row) => alert(`clicked ${row.name}`)}
          />
        </section>

        <section>
          <h2 className="mb-4 text-lg font-semibold">Empty state</h2>
          <div className="rounded-card bg-surface shadow-card">
            <EmptyState
              icon={FileText}
              message="No question papers yet"
              actionLabel="+ Upload paper"
              onAction={() => alert('upload clicked')}
            />
          </div>
        </section>

        <section>
          <h2 className="mb-4 text-lg font-semibold">Modal</h2>
          <Button onClick={() => setModalOpen(true)}>Open modal</Button>
          <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} title="New Project">
            <p className="text-sm text-text-secondary">
              Modal body content goes here.
            </p>
            <div className="mt-6 flex justify-end gap-3">
              <Button variant="secondary" onClick={() => setModalOpen(false)}>
                Cancel
              </Button>
              <Button onClick={() => setModalOpen(false)}>Create</Button>
            </div>
          </Modal>
        </section>
      </main>
    </div>
  );
}
