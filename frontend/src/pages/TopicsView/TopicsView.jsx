import { useCallback, useMemo } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { ListTree } from 'lucide-react';
import AppShell from '../../components/AppShell';
import EmptyState from '../../components/EmptyState';
import LoadingState from '../../components/LoadingState';
import ErrorState from '../../components/ErrorState';
import { useApiData } from '../../hooks/useApiData';
import { getProject } from '../../services/projectsService';
import { listProjectSyllabi, getSyllabusTopics } from '../../services/syllabiService';
import SyllabusSelector from './SyllabusSelector';
import TopicAccordion from './TopicAccordion';

// Topics are extracted per syllabus document, not merged across a project -
// there's no single "all topics" endpoint, so this screen is organized
// around the project's syllabus documents (see FRONTEND_DESIGN.md §5).
async function fetchProjectAndSyllabi(projectId) {
  const [project, syllabi] = await Promise.all([
    getProject(projectId),
    listProjectSyllabi(projectId),
  ]);
  return { project, syllabi };
}

export default function TopicsView() {
  const { projectId } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();

  const fetchBase = useCallback(() => fetchProjectAndSyllabi(projectId), [projectId]);
  const {
    data: baseData,
    isLoading: isBaseLoading,
    error: baseError,
    reload: reloadBase,
  } = useApiData(fetchBase);

  const requestedSyllabusId = searchParams.get('syllabusId');
  const selectedSyllabus = useMemo(() => {
    if (!baseData) return null;
    const match = baseData.syllabi.find((s) => s.id === requestedSyllabusId);
    return match ?? baseData.syllabi[0] ?? null;
  }, [baseData, requestedSyllabusId]);

  const fetchContent = useCallback(() => {
    return selectedSyllabus ? getSyllabusTopics(selectedSyllabus.id) : Promise.resolve(null);
  }, [selectedSyllabus]);
  const {
    data: content,
    isLoading: isContentLoading,
    error: contentError,
    reload: reloadContent,
  } = useApiData(fetchContent);

  return (
    <AppShell
      breadcrumb={[
        { label: 'Projects', href: '/projects' },
        { label: baseData?.project.name ?? projectId, href: `/projects/${projectId}` },
        { label: 'Topics' },
      ]}
    >
      <h1 className="text-2xl font-semibold text-text-primary">Topics</h1>

      {isBaseLoading && <LoadingState message="Loading topics…" className="mt-6" />}
      {baseError && (
        <ErrorState
          message={`Couldn't load topics: ${baseError.message}`}
          onRetry={reloadBase}
          className="mt-6"
        />
      )}

      {!isBaseLoading && !baseError && baseData && baseData.syllabi.length === 0 && (
        <div className="mt-6 rounded-card bg-surface shadow-card">
          <EmptyState icon={ListTree} message="No syllabus documents uploaded yet." />
        </div>
      )}

      {!isBaseLoading && !baseError && selectedSyllabus && (
        <>
          <div className="mt-6">
            <SyllabusSelector
              syllabi={baseData.syllabi}
              selectedId={selectedSyllabus.id}
              onSelect={(id) => setSearchParams({ syllabusId: id })}
            />
          </div>

          <p className="mt-4 text-sm text-text-muted">
            {selectedSyllabus.total_topics} topics · {selectedSyllabus.total_subtopics} subtopics
          </p>

          {isContentLoading && <LoadingState message="Loading topics…" className="mt-4" />}
          {contentError && (
            <ErrorState
              message={`Couldn't load topics: ${contentError.message}`}
              onRetry={reloadContent}
              className="mt-4"
            />
          )}

          {!isContentLoading && !contentError && content && content.content.length === 0 && (
            <div className="mt-4 rounded-card bg-surface shadow-card">
              <EmptyState icon={ListTree} message="No topics extracted yet for this document." />
            </div>
          )}

          {!isContentLoading && !contentError && content && content.content.length > 0 && (
            <div className="mt-4">
              <TopicAccordion key={selectedSyllabus.id} topics={content.content} />
            </div>
          )}
        </>
      )}
    </AppShell>
  );
}
