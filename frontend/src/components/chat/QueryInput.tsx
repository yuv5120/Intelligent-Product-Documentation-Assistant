import { useState, useRef, useEffect, type KeyboardEvent } from 'react';
import { ArrowUp } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';

export default function QueryInput() {
  const { sendMessage, isLoading, totalDocuments } = useAppStore();
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    ta.style.height = `${Math.min(ta.scrollHeight, 180)}px`;
  }, [value]);

  const canSend = value.trim().length > 0 && !isLoading;

  function handleSend() {
    const q = value.trim();
    if (!q || isLoading) return;
    setValue('');
    sendMessage(q);
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="query-input-area">
      <div className="query-input-wrap">
        <div className="query-input-box">
          <textarea
            ref={textareaRef}
            id="query-input"
            className="query-textarea"
            placeholder={
              totalDocuments === 0
                ? 'Upload documents first, then ask a question…'
                : 'Ask anything about your documentation…'
            }
            value={value}
            onChange={e => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            disabled={isLoading}
            aria-label="Query input"
          />
          <button
            id="send-btn"
            className="query-send-btn"
            onClick={handleSend}
            disabled={!canSend}
            aria-label="Send message"
          >
            <ArrowUp size={16} />
          </button>
        </div>
        <div className="query-meta">
          <span className="query-hint">
            Press <kbd>Enter</kbd> to send · <kbd>Shift+Enter</kbd> for new line
          </span>
          <span style={{ color: value.length > 1800 ? 'var(--warning)' : 'var(--text-muted)' }}>
            {value.length}/2000
          </span>
        </div>
      </div>
    </div>
  );
}
