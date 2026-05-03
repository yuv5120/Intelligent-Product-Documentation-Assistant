import { create } from 'zustand';
import { v4 as uuidv4 } from 'uuid';
import type { ChatMessage, Session, Toast, HealthStatus } from '../types/api';
import { api } from '../api/client';

interface AppState {
  // Sessions
  sessions: Session[];
  activeSessionId: string;

  // Messages per session
  messages: Record<string, ChatMessage[]>;

  // UI state
  isLoading: boolean;
  healthStatus: HealthStatus;
  totalDocuments: number;
  modelType: string;
  toasts: Toast[];
  showSettings: boolean;
  apiKey: string;

  // Actions
  newSession: () => void;
  setActiveSession: (id: string) => void;
  deleteSession: (id: string) => void;
  sendMessage: (query: string) => Promise<void>;
  uploadFile: (file: File) => Promise<void>;
  clearDatabase: () => Promise<void>;
  checkHealth: () => Promise<void>;
  addToast: (type: Toast['type'], message: string) => void;
  dismissToast: (id: string) => void;
  setShowSettings: (show: boolean) => void;
  setApiKey: (key: string) => void;
}

function sessionName(index: number): string {
  return `Session ${index + 1}`;
}

const INITIAL_SESSION_ID = uuidv4();

export const useAppStore = create<AppState>((set, get) => ({
  sessions: [{ id: INITIAL_SESSION_ID, name: 'Session 1', createdAt: new Date(), messageCount: 0 }],
  activeSessionId: INITIAL_SESSION_ID,
  messages: { [INITIAL_SESSION_ID]: [] },
  isLoading: false,
  healthStatus: 'loading',
  totalDocuments: 0,
  modelType: '',
  toasts: [],
  showSettings: false,
  apiKey: localStorage.getItem('api_key') ?? '',

  newSession: () => {
    const id = uuidv4();
    const { sessions } = get();
    const name = sessionName(sessions.length);
    set(s => ({
      sessions: [...s.sessions, { id, name, createdAt: new Date(), messageCount: 0 }],
      messages: { ...s.messages, [id]: [] },
      activeSessionId: id,
    }));
  },

  setActiveSession: (id) => set({ activeSessionId: id }),

  deleteSession: async (id) => {
    try { await api.clearSession(id); } catch { /* best-effort */ }
    set(s => {
      const sessions = s.sessions.filter(se => se.id !== id);
      const messages = { ...s.messages };
      delete messages[id];

      // If we deleted the active session or the list is now empty, create a fresh one
      if (sessions.length === 0 || s.activeSessionId === id) {
        if (sessions.length === 0) {
          const nid = uuidv4();
          const newSession = { id: nid, name: 'Session 1', createdAt: new Date(), messageCount: 0 };
          messages[nid] = [];
          return { sessions: [newSession], messages, activeSessionId: nid };
        }
        return { sessions, messages, activeSessionId: sessions[0].id };
      }

      return { sessions, messages, activeSessionId: s.activeSessionId };
    });
  },

  sendMessage: async (query: string) => {
    const { activeSessionId } = get();

    const userMsg: ChatMessage = {
      id: uuidv4(), role: 'user', content: query, timestamp: new Date(),
    };

    set(s => ({
      isLoading: true,
      messages: {
        ...s.messages,
        [activeSessionId]: [...(s.messages[activeSessionId] ?? []), userMsg],
      },
      sessions: s.sessions.map(se =>
        se.id === activeSessionId ? { ...se, messageCount: se.messageCount + 1 } : se
      ),
    }));

    try {
      const result = await api.query({ query, session_id: activeSessionId });
      const assistantMsg: ChatMessage = {
        id: uuidv4(), role: 'assistant',
        content: result.answer,
        sources: result.sources,
        timestamp: new Date(),
      };
      set(s => ({
        isLoading: false,
        messages: {
          ...s.messages,
          [activeSessionId]: [...(s.messages[activeSessionId] ?? []), assistantMsg],
        },
      }));
    } catch (err: unknown) {
      const detail = err instanceof Error ? err.message : 'Query failed';
      const errMsg: ChatMessage = {
        id: uuidv4(), role: 'assistant',
        content: `⚠️ ${detail}`,
        timestamp: new Date(),
        isError: true,
      };
      set(s => ({
        isLoading: false,
        messages: {
          ...s.messages,
          [activeSessionId]: [...(s.messages[activeSessionId] ?? []), errMsg],
        },
      }));
      get().addToast('error', detail);
    }
  },

  uploadFile: async (file: File) => {
    set({ isLoading: true });
    try {
      const result = await api.upload(file);
      set({ isLoading: false, totalDocuments: result.total_documents });
      get().addToast('success', `"${result.filename}" indexed — ${result.chunks_created} chunks added.`);
    } catch (err: unknown) {
      set({ isLoading: false });
      const detail = err instanceof Error ? err.message : 'Upload failed';
      get().addToast('error', detail);
    }
  },

  clearDatabase: async () => {
    try {
      const result = await api.clearDatabase();
      set({ totalDocuments: 0 });
      get().addToast('success', `Cleared ${result.documents_removed} document chunks.`);
    } catch (err: unknown) {
      const detail = err instanceof Error ? err.message : 'Clear failed';
      get().addToast('error', detail);
    }
  },

  checkHealth: async () => {
    set({ healthStatus: 'loading' });
    try {
      const h = await api.health();
      set({ healthStatus: 'healthy', totalDocuments: h.total_documents, modelType: h.model_type });
    } catch {
      set({ healthStatus: 'unhealthy' });
    }
  },

  addToast: (type, message) => {
    const id = uuidv4();
    set(s => ({ toasts: [...s.toasts, { id, type, message }] }));
    setTimeout(() => get().dismissToast(id), 5000);
  },

  dismissToast: (id) => set(s => ({ toasts: s.toasts.filter(t => t.id !== id) })),

  setShowSettings: (show) => set({ showSettings: show }),

  setApiKey: (key) => {
    localStorage.setItem('api_key', key);
    set({ apiKey: key });
  },
}));
