import { apiRequest } from './apiClient';

// Both run before we have a token, so auth: false skips the Authorization header.

export function login(email, password) {
  return apiRequest('/auth/login', { method: 'POST', json: { email, password }, auth: false });
}

export function signup(email, password) {
  return apiRequest('/auth/signup', { method: 'POST', json: { email, password }, auth: false });
}
