import { useEffect } from 'react';
import { Wifi, WifiOff, Loader2 } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';

export default function StatusBadge() {
  const { healthStatus, modelType, checkHealth } = useAppStore();

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30_000);
    return () => clearInterval(interval);
  }, []);

  if (healthStatus === 'loading') {
    return (
      <div className="status-badge loading">
        <Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} />
        <span>Connecting…</span>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  if (healthStatus === 'unhealthy') {
    return (
      <div className="status-badge unhealthy" title="Backend API is unreachable">
        <div className="status-dot" />
        <WifiOff size={12} />
        <span>Offline</span>
      </div>
    );
  }

  return (
    <div className="status-badge healthy" title={`Model: ${modelType}`}>
      <div className="status-dot" />
      <Wifi size={12} />
      <span>Connected · {modelType}</span>
    </div>
  );
}
