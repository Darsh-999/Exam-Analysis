import { apiRequest } from './apiClient';

export function getDocumentsStatus(projectId) {
  return apiRequest(`/projects/${projectId}/documents/status`);
}

// files: { questionPapers: File[], syllabi: File[] } - either can be omitted/empty
export function uploadDocuments(projectId, { questionPapers = [], syllabi = [] } = {}) {
  const formData = new FormData();
  questionPapers.forEach((file) => formData.append('question_papers', file));
  syllabi.forEach((file) => formData.append('syllabi', file));

  return apiRequest(`/projects/${projectId}/documents`, { method: 'POST', formData });
}
