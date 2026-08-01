import { apiRequest } from './apiClient';

export function getGlobalCounts() {
  return apiRequest('/analytics/counts');
}
