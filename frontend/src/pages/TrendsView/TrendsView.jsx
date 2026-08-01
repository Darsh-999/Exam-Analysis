import { useCallback, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import AppShell from '../../components/AppShell';
import LoadingState from '../../components/LoadingState';
import ErrorState from '../../components/ErrorState';
import { useApiData } from '../../hooks/useApiData';
import { getProject } from '../../services/projectsService';
import { listProjectQuestionPapers } from '../../services/questionPapersService';
import {
  getQuestionsPerYear,
  getTopicFrequency,
  getSubtopicFrequency,
  getTopicYearHeatmap,
  getMarksPerPaper,
  getAllocationHealth,
  getMarkDistribution,
} from '../../services/trendsService';
import { createColorAssigner } from './chartColors';
import TrendsSubNav from './TrendsSubNav';
import TrendSection from './TrendSection';
import SingleSeriesBarChart from './SingleSeriesBarChart';
import FrequencyPanel from './FrequencyPanel';
import TopicYearHeatmap from './TopicYearHeatmap';
import TopicDistributionChart from './TopicDistributionChart';
import MarksPerPaperChart from './MarksPerPaperChart';
import AllocationHealthChart from './AllocationHealthChart';

// Orders topics by total marks contributed across all papers (descending) so
// the shared topic->color map hands out colors 1-8 to the topics that matter
// most project-wide, before anything folds into "Other".
function topicsByTotalMarks(marksPerPaperChart) {
  const totals = new Map();
  for (const entry of marksPerPaperChart.data) {
    for (const segment of entry.segments) {
      totals.set(segment.topic, (totals.get(segment.topic) ?? 0) + segment.marks);
    }
  }
  return Array.from(totals.entries())
    .sort((a, b) => b[1] - a[1])
    .map(([topic]) => topic);
}

async function fetchTrendsData(projectId) {
  const [project, questionsPerYear, topicYearHeatmap, marksPerPaper, allocationHealth, markDistribution, questionPapers] =
    await Promise.all([
      getProject(projectId),
      getQuestionsPerYear(projectId),
      getTopicYearHeatmap(projectId),
      getMarksPerPaper(projectId),
      getAllocationHealth(projectId),
      getMarkDistribution(projectId),
      listProjectQuestionPapers(projectId),
    ]);
  return {
    project,
    questionsPerYear,
    topicYearHeatmap,
    marksPerPaper,
    allocationHealth,
    markDistribution,
    questionPapers,
  };
}

export default function TrendsView() {
  const { projectId } = useParams();

  const fetchData = useCallback(() => fetchTrendsData(projectId), [projectId]);
  const { data, isLoading, error, reload } = useApiData(fetchData);

  // Built once per data load and reused everywhere a topic needs a color on
  // this page (Topic Frequency bars, Topic Distribution pie, Marks per
  // Paper segments) - see FRONTEND_DESIGN.md §6.3.
  const topicColorMap = useMemo(() => {
    if (!data) return () => undefined;
    return createColorAssigner(topicsByTotalMarks(data.marksPerPaper));
  }, [data]);

  return (
    <AppShell
      breadcrumb={[
        { label: 'Projects', href: '/projects' },
        { label: data?.project.name ?? projectId, href: `/projects/${projectId}` },
        { label: 'Trends' },
      ]}
    >
      <h1 className="text-2xl font-semibold text-text-primary">Trend & Insights</h1>

      {isLoading && <LoadingState message="Loading trends…" className="mt-6" />}
      {error && (
        <ErrorState
          message={`Couldn't load trends: ${error.message}`}
          onRetry={reload}
          className="mt-6"
        />
      )}

      {!isLoading && !error && data && (
        <>
          <div className="mt-6">
            <TrendsSubNav />
          </div>

          <div className="space-y-8">
            <TrendSection id="content-trends" title="Content Trends">
              <SingleSeriesBarChart chart={data.questionsPerYear} />

              <div className="flex flex-col gap-6 lg:flex-row">
                <FrequencyPanel
                  projectId={projectId}
                  fetcher={getTopicFrequency}
                  colorMap={topicColorMap}
                />
                <FrequencyPanel projectId={projectId} fetcher={getSubtopicFrequency} />
              </div>

              <TopicYearHeatmap chart={data.topicYearHeatmap} />
            </TrendSection>

            <TrendSection id="papers" title="Papers">
              {data.questionPapers.length > 0 ? (
                <TopicDistributionChart papers={data.questionPapers} topicColorMap={topicColorMap} />
              ) : (
                <p className="text-sm text-text-muted">No question papers uploaded yet.</p>
              )}

              <MarksPerPaperChart chart={data.marksPerPaper} topicColorMap={topicColorMap} />
            </TrendSection>

            <TrendSection id="coverage" title="Coverage" muted>
              <AllocationHealthChart chart={data.allocationHealth} />
            </TrendSection>

            <TrendSection id="exam-structure" title="Exam Structure">
              <SingleSeriesBarChart chart={data.markDistribution} />
            </TrendSection>
          </div>
        </>
      )}
    </AppShell>
  );
}
