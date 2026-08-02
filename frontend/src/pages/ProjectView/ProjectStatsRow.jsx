import { FileText, BookOpen, Layers, HelpCircle, ListTree } from 'lucide-react';
import StatCard from '../../components/StatCard';

// summary: a ProjectSummaryOut from GET /projects/:id/summary
export default function ProjectStatsRow({ summary }) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
      <StatCard label="Question Papers" value={summary.total_question_papers} icon={FileText} />
      <StatCard label="Syllabi" value={summary.total_syllabi} icon={BookOpen} />
      <StatCard label="Subjects" value={summary.total_subjects} icon={Layers} />
      <StatCard label="Questions" value={summary.total_questions} icon={HelpCircle} />
      <StatCard label="Topics" value={summary.total_topics} icon={ListTree} />
    </div>
  );
}
