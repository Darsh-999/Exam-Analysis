import { apiRequest } from './apiClient';

export function listProjectQuestionPapers(projectId) {
  return apiRequest(`/projects/${projectId}/question-papers`);
}

export function listQuestionPaperQuestions(questionPaperId) {
  return apiRequest(`/question-papers/${questionPaperId}/questions`);
}

export function getQuestionPaperTopicDistribution(questionPaperId) {
  return apiRequest(`/question-papers/${questionPaperId}/trends/topic-distribution`);
}
