import { TOKEN_KEY } from '../context/AuthContext';

// Thrown for any non-2xx response. `status` is the HTTP status code,
// `detail` is the raw `detail` field from the backend's error body (handy
// if a screen wants to react to a specific status/detail instead of just
// showing `message`).
export class ApiError extends Error {
  constructor(message, { status, detail } = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

function buildQueryString(params) {
  if (!params) return '';
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      search.set(key, value);
    }
  }
  const query = search.toString();
  return query ? `?${query}` : '';
}

// FastAPI error bodies are usually `{ detail: "some message" }`, but
// validation errors (422) come back as `{ detail: [{ msg, loc, type }] }`.
// This normalizes both into a single readable string.
function extractErrorMessage(data, fallback) {
  if (!data || data.detail === undefined) return fallback;
  if (typeof data.detail === 'string') return data.detail;
  if (Array.isArray(data.detail)) {
    return data.detail.map((issue) => issue.msg).join('; ');
  }
  return fallback;
}

/**
 * Thin fetch wrapper for every backend call in the app.
 *
 * @param {string} path - starts with '/', e.g. '/projects' (NOT '/api/projects' - that's added here)
 * @param {object} [options]
 * @param {string} [options.method] - 'GET' (default), 'POST', 'DELETE', ...
 * @param {object} [options.json] - request body, sent as JSON
 * @param {FormData} [options.formData] - request body for file uploads (mutually exclusive with json)
 * @param {object} [options.params] - query-string params; undefined/null/'' values are skipped
 * @param {boolean} [options.auth] - set to false for login/signup, which run before a token exists
 */
export async function apiRequest(
  path,
  { method = 'GET', json, formData, params, auth = true } = {}
) {
  const headers = {};
  let body;

  if (formData) {
    // Don't set Content-Type ourselves - the browser adds the multipart
    // boundary automatically when the body is a FormData instance.
    body = formData;
  } else if (json !== undefined) {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(json);
  }

  if (auth) {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`/api${path}${buildQueryString(params)}`, {
    method,
    headers,
    body,
  });

  if (response.status === 204) return null;

  const text = await response.text();
  const data = text ? JSON.parse(text) : null;

  if (!response.ok) {
    throw new ApiError(extractErrorMessage(data, response.statusText), {
      status: response.status,
      detail: data?.detail,
    });
  }

  return data;
}
