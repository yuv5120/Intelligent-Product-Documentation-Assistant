// All TypeScript interfaces matching the FastAPI backend models

export interface Source {
  citation: string;   // "[1] manual.pdf (section 2)"
  filename: string;
  chunk_index: number;
}

export interface QueryRequest {
  query: string;
  session_id?: string;
  top_k?: number;
  top_n?: number;
}

export interface QueryResponse {
  answer: string;
  sources: Source[];
  context_used: number;
  session_id: string;
}

export interface UploadResponse {
  message: string;
  filename: string;
  chunks_created: number;
  total_documents: number;
}

export interface HealthResponse {
  status: string;
  model_type: string;
  total_documents: number;
  session_backend: string;
}

export interface ClearResponse {
  message: string;
  documents_removed: number;
}

export interface ErrorResponse {
  detail: string;
}

// Frontend-only types
export type MessageRole = 'user' | 'assistant';

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  sources?: Source[];
  timestamp: Date;
  isError?: boolean;
}

export interface Session {
  id: string;
  name: string;
  createdAt: Date;
  messageCount: number;
}

export type ToastType = 'success' | 'error';

export interface Toast {
  id: string;
  type: ToastType;
  message: string;
}

export type HealthStatus = 'healthy' | 'unhealthy' | 'loading';
