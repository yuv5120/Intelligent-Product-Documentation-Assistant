import { useAppStore } from '../../store/useAppStore';
import { BookOpen, Settings } from 'lucide-react';
import StatusBadge from '../ui/StatusBadge';

export default function Header() {
  const { setShowSettings } = useAppStore();

  return (
    <header className="header">
      <div className="header-logo">
        <div className="header-logo-icon">
          <BookOpen size={15} color="white" />
        </div>
        <span>DocAssist AI</span>
      </div>

      <div className="header-actions">
        <StatusBadge />
        <button
          className="btn btn-ghost"
          onClick={() => setShowSettings(true)}
          id="settings-btn"
          title="Settings"
        >
          <Settings size={15} />
          <span>Settings</span>
        </button>
      </div>
    </header>
  );
}
