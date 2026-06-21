import React from 'react';
import './ChatWindow.css';

function ChatWindow({ 
  messages, 
  loading, 
  onSendMessage, 
  uploadedFile, 
  onClearFile,
  input,
  setInput,
  showInput
}) {
  const messagesEndRef = React.useRef(null);

  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="chat-window">
      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message message-${msg.role}`}>
            <div className="message-content">
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="message message-assistant">
            <div className="message-content">
              <span className="typing-indicator">● ● ●</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {showInput && (
        <form onSubmit={onSendMessage} className="input-form">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            className="chat-input"
            disabled={loading}
            autoFocus
          />
          <button 
            type="submit" 
            className="send-button"
            disabled={loading || !input.trim()}
          >
            ↑
          </button>
        </form>
      )}

      {uploadedFile && (
        <div className="file-indicator">
          📎 {uploadedFile}
          <button 
            onClick={onClearFile}
            className="clear-file"
            type="button"
          >
            ✕
          </button>
        </div>
      )}
    </div>
  );
}

export default ChatWindow;
