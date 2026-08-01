import { useCallback, useState } from 'react';
import { useParams } from 'react-router-dom';
import { FileText, BookOpen } from 'lucide-react';
import AppShell from '../../components/AppShell';
import EmptyState from '../../components/EmptyState';
import LoadingState from '../../components/LoadingState';
import ErrorState from '../../components/ErrorState';
import { useApiData } from '../../hooks/useApiData';
import { usePolling } from '../../hooks/usePolling';
import { getProjectSummary } from '../../services/projectsService';
import { listProjectQuestionPapers } from '../../services/questionPapersService';
import { listProjectSyllabi } from '../../services/syllabiService';
import ProjectHeader from './ProjectHeader';
import ProjectStatsRow from './ProjectStatsRow';
import ProjectActionsRow from './ProjectActionsRow';
import QuestionPapersTable from './QuestionPapersTable';
import SyllabusTable from './SyllabusTable';
import UploadMoreModal from './UploadMoreModal';

const STILL_PROCESSING = new Set(['extracting', 'classifying']);
const POLL_INTERVAL_MS = 4000;

async function fetchProjectView(projectId) {
  const [summary, papers, syllabi] = await Promise.all([
    getProjectSummary(projectId),
    listProjectQuestionPapers(projectId),
    listProjectSyllabi(projectId),
  ]);
  return { summary, papers, syllabi };
}

export default function ProjectView() {
  const { projectId } = useParams();
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

  const fetchData = useCallback(() => fetchProjectView(projectId), [projectId]);
  const { data, isLoading, error, reload } = useApiData(fetchData);

  const processingCount = data
    ? [...data.papers, ...data.syllabi].filter((doc) => STILL_PROCESSING.has(doc.status)).length
    : 0;

  // Keep the stat cards and tables live while anything is still
  // extracting/classifying; stop as soon as everything settles.
  usePolling(processingCount > 0, reload, POLL_INTERVAL_MS);

  return (
    <AppShell
      breadcrumb={[
        { label: 'Projects', href: '/projects' },
        { label: data?.summary.name ?? projectId },
      ]}
    >
      {isLoading && <LoadingState message="Loading project…" />}

      {error && (
        <ErrorState message={`Couldn't load this project: ${error.message}`} onRetry={reload} />
      )}

      {!isLoading && !error && data && (
        <>
          <ProjectHeader summary={data.summary} onUploadMoreClick={() => setIsUploadModalOpen(true)} />

          {processingCount > 0 && (
            <p className="mt-4 rounded-btn bg-warning/10 px-4 py-2 text-sm text-warning">
              Processing {processingCount} document{processingCount === 1 ? '' : 's'}... this
              page will update automatically.
            </p>
          )}

          <div className="mt-6">
            <ProjectStatsRow summary={data.summary} />
          </div>

          <div className="mt-6">
            <ProjectActionsRow projectId={projectId} />
          </div>

          <div className="mt-8">
            <h2 className="mb-3 text-lg font-semibold text-text-primary">Question Papers</h2>
            {data.papers.length > 0 ? (
              <QuestionPapersTable papers={data.papers} />
            ) : (
              <div className="rounded-card bg-surface shadow-card">
                <EmptyState icon={FileText} message="No question papers uploaded yet." />
              </div>
            )}
          </div>

          <div className="mt-8">
            <h2 className="mb-3 text-lg font-semibold text-text-primary">Syllabus</h2>
            {data.syllabi.length > 0 ? (
              <SyllabusTable projectId={projectId} syllabi={data.syllabi} />
            ) : (
              <div className="rounded-card bg-surface shadow-card">
                <EmptyState icon={BookOpen} message="No syllabus documents uploaded yet." />
              </div>
            )}
          </div>
        </>
      )}

      <UploadMoreModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        projectId={projectId}
        onUploaded={reload}
      />
    </AppShell>
  );
}
