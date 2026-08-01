import { apiRequest } from './apiClient';

export function getQuestionsPerYear(projectId) {
  return apiRequest(`/projects/${projectId}/trends/questions-per-year`);
}

// metric: 'count' (default) | 'marks'
export function getTopicFrequency(projectId, metric = 'count') {
  return apiRequest(`/projects/${projectId}/trends/topic-frequency`, { params: { metric } });
}

export function getSubtopicFrequency(projectId, metric = 'count') {
  return apiRequest(`/projects/${projectId}/trends/subtopic-frequency`, { params: { metric } });
}

export function getMarksPerPaper(projectId) {
  return apiRequest(`/projects/${projectId}/trends/marks-per-paper`);
}

export function getTopicYearHeatmap(projectId) {
  return apiRequest(`/projects/${projectId}/trends/topic-year-heatmap`);
}

export function getAllocationHealth(projectId) {
  return apiRequest(`/projects/${projectId}/trends/allocation-health`);
}

export function getMarkDistribution(projectId) {
  return apiRequest(`/projects/${projectId}/trends/mark-distribution`);
}
