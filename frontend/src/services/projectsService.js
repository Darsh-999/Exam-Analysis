import { apiRequest } from './apiClient';

export function listProjects() {
  return apiRequest('/projects');
}

export function listProjectIds() {
  return apiRequest('/projects/ids');
}

export function getProject(projectId) {
  return apiRequest(`/projects/${projectId}`);
}

export function getProjectSummary(projectId) {
  return apiRequest(`/projects/${projectId}/summary`);
}

export function createProject({ name, description }) {
  return apiRequest('/projects', { method: 'POST', json: { name, description } });
}

export function deleteProject(projectId) {
  return apiRequest(`/projects/${projectId}`, { method: 'DELETE' });
}
