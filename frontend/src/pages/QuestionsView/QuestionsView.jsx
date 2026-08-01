import { useCallback, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import { HelpCircle } from 'lucide-react';
import AppShell from '../../components/AppShell';
import EmptyState from '../../components/EmptyState';
import LoadingState from '../../components/LoadingState';
import ErrorState from '../../components/ErrorState';
import { useApiData } from '../../hooks/useApiData';
import { getProject } from '../../services/projectsService';
import { listProjectQuestions } from '../../services/questionsService';
import QuestionsFilterBar from './QuestionsFilterBar';
import QuestionCard from './QuestionCard';

function allocationStatusOf(question) {
  if (question.topic.length === 0) return 'unallocated';
  if (question.topic.length === 1) return 'allocated';
  return 'multi_allocated';
}

function encodeSubject(name, code) {
  return `${name ?? ''}||${code ?? ''}`;
}

async function fetchQuestionsData(projectId) {
  const [project, questions] = await Promise.all([
    getProject(projectId),
    listProjectQuestions(projectId),
  ]);
  return { project, questions };
}

export default function QuestionsView() {
  const { projectId } = useParams();

  const [subjectFilter, setSubjectFilter] = useState('');
  const [topicFilter, setTopicFilter] = useState('');
  const [allocationFilter, setAllocationFilter] = useState('');
  const [keyword, setKeyword] = useState('');

  const fetchData = useCallback(() => fetchQuestionsData(projectId), [projectId]);
  const { data, isLoading, error, reload } = useApiData(fetchData);

  const subjectOptions = useMemo(() => {
    if (!data) return [];
    const seen = new Map();
    for (const q of data.questions) {
      const value = encodeSubject(q.subject_name, q.subject_code);
      if (!seen.has(value) && q.subject_name) {
        seen.set(value, `${q.subject_name} (${q.subject_code ?? '—'})`);
      }
    }
    return Array.from(seen, ([value, label]) => ({ value, label }));
  }, [data]);

  const topicOptions = useMemo(() => {
    if (!data) return [];
    const topics = new Set();
    for (const q of data.questions) {
      for (const t of q.topic) topics.add(t.topic);
    }
    return Array.from(topics).sort();
  }, [data]);

  const filteredQuestions = useMemo(() => {
    if (!data) return [];
    const keywordQuery = keyword.trim().toLowerCase();
    const topicQuery = topicFilter.trim().toLowerCase();

    return data.questions.filter((q) => {
      if (subjectFilter && encodeSubject(q.subject_name, q.subject_code) !== subjectFilter) {
        return false;
      }
      if (topicQuery && !q.topic.some((t) => t.topic.toLowerCase().includes(topicQuery))) {
        return false;
      }
      if (allocationFilter && allocationStatusOf(q) !== allocationFilter) {
        return false;
      }
      if (keywordQuery && !q.question.toLowerCase().includes(keywordQuery)) {
        return false;
      }
      return true;
    });
  }, [data, subjectFilter, topicFilter, allocationFilter, keyword]);

  return (
    <AppShell
      breadcrumb={[
        { label: 'Projects', href: '/projects' },
        { label: data?.project.name ?? projectId, href: `/projects/${projectId}` },
        { label: 'Questions' },
      ]}
    >
      <h1 className="text-2xl font-semibold text-text-primary">Questions</h1>

      {isLoading && <LoadingState message="Loading questions…" className="mt-6" />}
      {error && (
        <ErrorState
          message={`Couldn't load questions: ${error.message}`}
          onRetry={reload}
          className="mt-6"
        />
      )}

      {!isLoading && !error && data && (
        <>
          <div className="mt-6">
            <QuestionsFilterBar
              subjects={subjectOptions}
              topics={topicOptions}
              subjectValue={subjectFilter}
              onSubjectChange={setSubjectFilter}
              topicValue={topicFilter}
              onTopicChange={setTopicFilter}
              allocationValue={allocationFilter}
              onAllocationChange={setAllocationFilter}
              keywordValue={keyword}
              onKeywordChange={setKeyword}
            />
          </div>

          <p className="mt-3 text-sm text-text-muted">
            Showing {filteredQuestions.length} question{filteredQuestions.length === 1 ? '' : 's'}
          </p>

          {filteredQuestions.length === 0 ? (
            <div className="mt-6 rounded-card bg-surface shadow-card">
              <EmptyState icon={HelpCircle} message="No questions match these filters." />
            </div>
          ) : (
            <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {filteredQuestions.map((question) => (
                <QuestionCard key={question.question_id} question={question} />
              ))}
            </div>
          )}
        </>
      )}
    </AppShell>
  );
}
