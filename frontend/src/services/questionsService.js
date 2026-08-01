import { apiRequest } from './apiClient';

// filters (all optional, combine with AND): subjectName, subjectCode, topic,
// allocationStatus ('allocated' | 'unallocated' | 'multi_allocated')
export function listProjectQuestions(projectId, filters = {}) {
  const { subjectName, subjectCode, topic, allocationStatus } = filters;

  return apiRequest(`/projects/${projectId}/questions`, {
    params: {
      subject_name: subjectName,
      subject_code: subjectCode,
      topic,
      allocation_status: allocationStatus,
    },
  });
}
