import type {
  QueryRequest,
  QueryResponse,
  UploadResponse,
  HealthResponse,
  ClearResponse,
} from '../types/api';

// Read from localStorage first (set via Settings panel), then env var, then default
function getBaseUrl(): string {
  return (
    localStorage.getItem('api_base_url') ??
    import.meta.env.VITE_API_BASE_URL ??
    'http://localhost:8000'
  );
}

function getApiKey(): string {
  return localStorage.getItem('api_key') ?? '';
}

function buildHeaders(extra?: Record<string, string>): HeadersInit {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...extra,
  };
  const key = getApiKey();
  if (key) headers['X-API-Key'] = key;
  return headers;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const err = await res.json();
      detail = err.detail ?? detail;
    } catch { /* ignore parse errors */ }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  async health(): Promise<HealthResponse> {
    const res = await fetch(`${getBaseUrl()}/health`);
    return handleResponse<HealthResponse>(res);
  },

  async query(body: QueryRequest): Promise<QueryResponse> {
    const res = await fetch(`${getBaseUrl()}/query`, {
      method: 'POST',
      headers: buildHeaders(),
      body: JSON.stringify(body),
    });
    return handleResponse<QueryResponse>(res);
  },

  async upload(file: File): Promise<UploadResponse> {
    const form = new FormData();
    form.append('file', file);
    const headers: Record<string, string> = {};
    const key = getApiKey();
    if (key) headers['X-API-Key'] = key;
    const res = await fetch(`${getBaseUrl()}/upload`, {
      method: 'POST',
      headers,
      body: form,
    });
    return handleResponse<UploadResponse>(res);
  },

  async clearDatabase(): Promise<ClearResponse> {
    const res = await fetch(`${getBaseUrl()}/clear`, {
      method: 'DELETE',
      headers: buildHeaders(),
    });
    return handleResponse<ClearResponse>(res);
  },

  async clearSession(sessionId: string): Promise<void> {
    const res = await fetch(`${getBaseUrl()}/sessions/${encodeURIComponent(sessionId)}`, {
      method: 'DELETE',
      headers: buildHeaders(),
    });
    await handleResponse<unknown>(res);
  },
};
