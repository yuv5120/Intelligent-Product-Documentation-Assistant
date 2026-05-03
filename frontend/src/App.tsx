import { useState } from 'react';
import { X, Key } from 'lucide-react';
import { useAppStore } from './store/useAppStore';
import Header from './components/layout/Header';
import Sidebar from './components/layout/Sidebar';
import ChatWindow from './components/chat/ChatWindow';
import ToastContainer from './components/ui/Toast';
import { ErrorBoundary } from './components/ui/ErrorBoundary';

function SettingsPanel() {
  const { apiKey, setApiKey, setShowSettings } = useAppStore();
  const [localKey, setLocalKey] = useState(apiKey);
  const [baseUrl, setBaseUrl] = useState(
    localStorage.getItem('api_base_url') ?? 'http://localhost:8000'
  );

  function handleSave() {
    setApiKey(localKey);
    localStorage.setItem('api_base_url', baseUrl);
    setShowSettings(false);
  }

  return (
    <div className="settings-overlay" onClick={() => setShowSettings(false)}>
      <div className="settings-panel" onClick={e => e.stopPropagation()}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 16 }}>
          <div>
            <h2>Settings</h2>
            <p style={{ marginBottom: 0 }}>Configure your API connection</p>
          </div>
          <button className="btn btn-ghost" style={{ padding: 6 }} onClick={() => setShowSettings(false)}>
            <X size={16} />
          </button>
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="api-base-url">Backend URL</label>
          <input
            id="api-base-url"
            className="form-input"
            type="url"
            value={baseUrl}
            onChange={e => setBaseUrl(e.target.value)}
            placeholder="http://localhost:8000"
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="api-key-input">
            <Key size={11} style={{ display: 'inline', marginRight: 4 }} />
            API Key
          </label>
          <input
            id="api-key-input"
            className="form-input"
            type="password"
            value={localKey}
            onChange={e => setLocalKey(e.target.value)}
            placeholder="Leave blank if API_KEY is not set in .env"
          />
          <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6, lineHeight: 1.5 }}>
            Only required if <code style={{ background: 'var(--bg-elevated)', padding: '1px 4px', borderRadius: 3 }}>API_KEY</code> is
            configured in your backend <code style={{ background: 'var(--bg-elevated)', padding: '1px 4px', borderRadius: 3 }}>.env</code>.
          </p>
        </div>

        <div className="settings-actions">
          <button className="btn btn-ghost" onClick={() => setShowSettings(false)}>Cancel</button>
          <button className="btn btn-primary" onClick={handleSave} id="save-settings-btn">Save</button>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const { showSettings } = useAppStore();

  return (
    <ErrorBoundary>
      <div className="app-root">
        <ErrorBoundary fallback={<div style={{ padding: 16, color: 'var(--error)' }}>Sidebar error</div>}>
          <Sidebar />
        </ErrorBoundary>

        <div className="main-area">
          <Header />
          <ErrorBoundary fallback={<div style={{ padding: 32, textAlign: 'center', color: 'var(--text-secondary)' }}>Chat failed to load. Please refresh.</div>}>
            <ChatWindow />
          </ErrorBoundary>
        </div>

        {showSettings && <SettingsPanel />}
        <ToastContainer />
      </div>
    </ErrorBoundary>
  );
}
