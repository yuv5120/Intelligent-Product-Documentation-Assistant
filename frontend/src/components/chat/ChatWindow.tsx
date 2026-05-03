import { useEffect, useRef } from 'react';
import { Bot, Upload } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';
import QueryInput from './QueryInput';

const SUGGESTIONS = [
  'What are the main features?',
  'How do I get started?',
  'What is the warranty policy?',
  'How do I reset the device?',
];

export default function ChatWindow() {
  const { messages, activeSessionId, isLoading, sendMessage, totalDocuments } = useAppStore();
  const msgs = messages[activeSessionId] ?? [];
  const bottomRef = useRef<HTMLDivElement>(null);
  const hasDocuments = totalDocuments > 0;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [msgs.length, isLoading]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
      <div className="chat-window">
        <div className="chat-inner">
          {msgs.length === 0 ? (
            <div className="chat-empty">
              <div className="chat-empty-icon">
                <Bot size={28} color="var(--primary)" />
              </div>
              <h2>Ask about your documentation</h2>
              <p>
                {hasDocuments
                  ? 'Your documents are indexed and ready. Ask any question below.'
                  : 'Upload your product docs first, then ask any question — answers come with source citations.'}
              </p>

              {!hasDocuments && (
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    padding: '10px 16px',
                    borderRadius: 'var(--radius)',
                    background: 'var(--primary-dim)',
                    border: '1px solid rgba(99,102,241,0.2)',
                    fontSize: 13,
                    color: 'var(--primary-hover)',
                    marginTop: 4,
                  }}
                >
                  <Upload size={13} />
                  Use the upload panel on the left to index your documents
                </div>
              )}

              <div className="chat-empty-suggestions">
                {SUGGESTIONS.map(s => (
                  <button
                    key={s}
                    className="suggestion-chip"
                    onClick={() => hasDocuments && sendMessage(s)}
                    disabled={!hasDocuments || isLoading}
                    title={!hasDocuments ? 'Upload documents first' : s}
                    style={{
                      opacity: hasDocuments ? 1 : 0.4,
                      cursor: hasDocuments ? 'pointer' : 'not-allowed',
                    }}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {msgs.map(msg => (
                <MessageBubble key={msg.id} message={msg} />
              ))}
              {isLoading && (
                <div className="message-row">
                  <div className="message-avatar assistant">
                    <Bot size={15} />
                  </div>
                  <div className="message-content">
                    <TypingIndicator />
                  </div>
                </div>
              )}
            </>
          )}
          <div ref={bottomRef} />
        </div>
      </div>

      <QueryInput />
    </div>
  );
}
