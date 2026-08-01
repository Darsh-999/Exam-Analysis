import { useCallback } from 'react';
import { FolderKanban, FileText, BookOpen, Layers, HelpCircle, ListTree } from 'lucide-react';
import StatCard from '../../components/StatCard';
import { getGlobalCounts } from '../../services/analyticsService';
import { useApiData } from '../../hooks/useApiData';

const STAT_CONFIG = [
  { key: 'total_projects', label: 'Total Projects', icon: FolderKanban },
  { key: 'total_question_papers', label: 'Total Question Papers', icon: FileText },
  { key: 'total_syllabi', label: 'Total Syllabi', icon: BookOpen },
  { key: 'total_subjects', label: 'Total Subjects', icon: Layers },
  { key: 'total_questions', label: 'Total Questions', icon: HelpCircle },
  { key: 'total_topics', label: 'Total Topics', icon: ListTree },
];

export default function ProjectsStatsRow() {
  const fetchCounts = useCallback(() => getGlobalCounts(), []);
  const { data: counts } = useApiData(fetchCounts);

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
      {STAT_CONFIG.map(({ key, label, icon }) => (
        <StatCard key={key} label={label} value={counts ? counts[key] : '—'} icon={icon} />
      ))}
    </div>
  );
}
