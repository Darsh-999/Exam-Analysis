import { FileText, BookOpen, Layers, HelpCircle, ListTree } from 'lucide-react';
import StatCard from '../../components/StatCard';

// Cards 6 and 7 from the spec (Allocated / Unallocated Questions) are
// combined into one stacked-bar card here instead of two plain numbers -
// easier to scan at a glance than two separate counts.
function AllocationCard({ allocated, unallocated }) {
  const total = allocated + unallocated || 1;
  const allocatedPercent = (allocated / total) * 100;

  return (
    <div className="relative min-h-[140px] overflow-hidden rounded-card bg-surface p-5 shadow-card">
      <span className="absolute inset-y-0 left-0 w-1 bg-linear-to-b from-primary to-primary-amber" />
      <div className="flex h-full flex-col justify-between pl-3">
        <div>
          <div className="h-3 w-full overflow-hidden rounded-full bg-border">
            <div className="h-full bg-success" style={{ width: `${allocatedPercent}%` }} />
          </div>
          <p className="mt-3 text-sm text-text-primary">
            <span className="font-semibold text-success">{allocated}</span> allocated{' · '}
            <span className="font-semibold text-text-muted">{unallocated}</span> unallocated
          </p>
        </div>
        <span className="text-xs font-medium uppercase tracking-wide text-text-secondary">
          Allocation Coverage
        </span>
      </div>
    </div>
  );
}

// summary: a ProjectSummaryOut from GET /projects/:id/summary
export default function ProjectStatsRow({ summary }) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
      <StatCard label="Question Papers" value={summary.total_question_papers} icon={FileText} />
      <StatCard label="Syllabi" value={summary.total_syllabi} icon={BookOpen} />
      <StatCard label="Subjects" value={summary.total_subjects} icon={Layers} />
      <StatCard label="Questions" value={summary.total_questions} icon={HelpCircle} />
      <StatCard label="Topics" value={summary.total_topics} icon={ListTree} />
      <AllocationCard
        allocated={summary.total_allocated_questions}
        unallocated={summary.total_unallocated_questions}
      />
    </div>
  );
}
