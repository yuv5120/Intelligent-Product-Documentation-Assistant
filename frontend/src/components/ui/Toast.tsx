import { CheckCircle2, XCircle, X } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';

export default function ToastContainer() {
  const { toasts, dismissToast } = useAppStore();

  if (toasts.length === 0) return null;

  return (
    <div className="toast-container" role="region" aria-label="Notifications">
      {toasts.map(toast => (
        <div key={toast.id} className={`toast ${toast.type}`} role="alert">
          <div className="toast-icon">
            {toast.type === 'success'
              ? <CheckCircle2 size={16} />
              : <XCircle size={16} />}
          </div>
          <p className="toast-msg">{toast.message}</p>
          <button className="toast-close" onClick={() => dismissToast(toast.id)} aria-label="Dismiss">
            <X size={14} />
          </button>
        </div>
      ))}
    </div>
  );
}
