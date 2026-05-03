import { MessageSquare, Plus, Trash2, Database } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import UploadZone from '../upload/UploadZone';

export default function Sidebar() {
  const {
    sessions, activeSessionId, totalDocuments,
    newSession, setActiveSession, deleteSession, clearDatabase,
  } = useAppStore();

  function formatDate(d: Date) {
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <span className="sidebar-title">Conversations</span>
        <button className="btn-new-chat" onClick={newSession} id="new-chat-btn">
          <Plus size={14} />
          New Chat
        </button>
      </div>

      <div className="sidebar-body">
        <span className="sidebar-section-label">Recent</span>
        {sessions.map((session) => (
          <div
            key={session.id}
            className={`session-item${activeSessionId === session.id ? ' active' : ''}`}
            onClick={() => setActiveSession(session.id)}
            id={`session-${session.id}`}
          >
            <MessageSquare size={14} className="session-item-icon" />
            <div className="session-item-text">
              <div className="session-item-name">{session.name}</div>
              <div className="session-item-meta">
                {session.messageCount > 0
                  ? `${session.messageCount} message${session.messageCount !== 1 ? 's' : ''}`
                  : formatDate(session.createdAt)}
              </div>
            </div>
            <button
              className="session-delete-btn"
              onClick={(e) => { e.stopPropagation(); deleteSession(session.id); }}
              title="Delete session"
            >
              <Trash2 size={13} />
            </button>
          </div>
        ))}
      </div>

      <div className="sidebar-footer">
        <div className="divider" style={{ marginBottom: 12 }} />

        {/* Upload Zone */}
        <UploadZone />

        {/* Document count */}
        {totalDocuments > 0 && (
          <div className="doc-count-badge">
            <Database size={11} />
            {totalDocuments.toLocaleString()} document chunks indexed
          </div>
        )}

        {/* Clear DB */}
        {totalDocuments > 0 && (
          <div style={{ padding: '0 12px 4px' }}>
            <button
              className="btn btn-ghost btn-danger"
              style={{ width: '100%', justifyContent: 'center', fontSize: 12 }}
              onClick={() => {
                if (confirm('Delete all indexed documents? This cannot be undone.')) {
                  clearDatabase();
                }
              }}
              id="clear-db-btn"
            >
              <Trash2 size={12} />
              Clear all documents
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}
