import { apiRequest } from './apiClient';

export function listProjectSyllabi(projectId) {
  return apiRequest(`/projects/${projectId}/syllabi`);
}

export function getSyllabusTopics(syllabusId) {
  return apiRequest(`/syllabi/${syllabusId}/topics`);
}
