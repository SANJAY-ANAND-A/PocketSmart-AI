const TOKEN_KEY = 'pocketsmart_token';
const API_BASE_URL = '/api';

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

export function getStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setStoredToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {
    // Ignore storage errors in private/incognito if restricted
  }
}

export function removeStoredToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    // Ignore storage errors
  }
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  body?: unknown;
  headers?: Record<string, string>;
  token?: string | null;
}

export async function apiClient<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, headers = {}, token = getStoredToken() } = options;

  const url = endpoint.startsWith('http')
    ? endpoint
    : `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  const requestHeaders: Record<string, string> = { ...headers };

  if (token) {
    requestHeaders['Authorization'] = `Bearer ${token}`;
  }

  const isFormData = body instanceof FormData;

  let requestBody: BodyInit | undefined;
  if (body !== undefined) {
    if (isFormData) {
      requestBody = body;
      // CRITICAL: Do NOT set Content-Type header when sending FormData!
      // The browser must automatically set it with boundary.
      delete requestHeaders['Content-Type'];
    } else {
      requestHeaders['Content-Type'] = 'application/json';
      requestBody = JSON.stringify(body);
    }
  }

  const response = await fetch(url, {
    method,
    headers: requestHeaders,
    body: requestBody,
  });

  // Handle 204 No Content
  if (response.status === 204) {
    return {} as T;
  }

  // Attempt to parse JSON response
  let data: unknown;
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    try {
      data = await response.json();
    } catch {
      data = null;
    }
  } else {
    data = await response.text();
  }

  if (!response.ok) {
    let errorMessage = `HTTP Error ${response.status}`;

    if (data && typeof data === 'object') {
      const errorObj = data as { detail?: unknown; message?: string };
      if (typeof errorObj.detail === 'string') {
        errorMessage = errorObj.detail;
      } else if (Array.isArray(errorObj.detail)) {
        // FastAPI validation errors: [{ loc: [...], msg: "...", type: "..." }]
        const details = errorObj.detail
          .map((item: { msg?: string; loc?: string[] }) => {
            const loc = item.loc ? item.loc[item.loc.length - 1] : '';
            return loc ? `${loc}: ${item.msg}` : item.msg;
          })
          .filter(Boolean)
          .join(', ');
        errorMessage = details || 'Validation error';
      } else if (typeof errorObj.message === 'string') {
        errorMessage = errorObj.message;
      }
    } else if (typeof data === 'string' && data.length > 0) {
      errorMessage = data;
    }

    throw new ApiError(errorMessage, response.status, data);
  }

  return data as T;
}
