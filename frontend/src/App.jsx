import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [selectedModel, setSelectedModel] = useState('phi3.5');
  const [models, setModels] = useState({});
  const [loading, setLoading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [fileContext, setFileContext] = useState(null);
  const [fileType, setFileType] = useState(null);
  const [currentIntent, setCurrentIntent] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [showTextInput, setShowTextInput] = useState(false);

  const API_URL = 'http://localhost:8000';

  // Initial suggestions (support intents as inline buttons)
  const initialSuggestions = [
    { code: 'ORDER_STATUS', label: 'Check Order Status', icon: '📦', type: 'intent' },
    { code: 'DELIVERY_TRACKING', label: 'Track My Delivery', icon: '🚚', type: 'intent' },
    { code: 'RETURN_REQUEST', label: 'Return or Refund', icon: '↩️', type: 'intent' },
    { code: 'CANCEL_ORDER', label: 'Cancel My Order', icon: '❌', type: 'intent' },
    { code: 'DELIVERY_DELAY', label: 'Delivery Delay', icon: '⏰', type: 'intent' },
    { code: 'DAMAGED_ITEM', label: 'Damaged Item', icon: '💔', type: 'intent' },
    { code: 'MISSING_ITEM', label: 'Missing Item', icon: '🔍', type: 'intent' },
    { code: 'TAX_CUSTOMS', label: 'Tax & Customs', icon: '🌍', type: 'intent' },
    { code: 'INTERNATIONAL_SHIPPING', label: 'International', icon: '✈️', type: 'intent' },
    { code: 'PERISHABLE_PRODUCT', label: 'Perishable Items', icon: '❄️', type: 'intent' },
    { code: 'PAYMENT_ISSUE', label: 'Payment Issue', icon: '💳', type: 'intent' },
    { code: 'OTHER', label: 'Other Question', icon: '💬', type: 'intent' },
  ];

  useEffect(() => {
    fetch(`${API_URL}/api/models`)
      .then(res => res.json())
      .then(data => setModels(data.models))
      .catch(err => console.error('Failed to load models:', err));

    setSuggestions(initialSuggestions);
    setMessages([
      { role: 'assistant', content: 'Hello! How can we help you today? Click any option below or type your question.' }
    ]);
  }, []);

  const getContextSuggestions = (intentCode) => {
    const contextMap = {
      'ORDER_STATUS': [
        { label: 'ORD12345', type: 'direct' },
        { label: 'ORD12346', type: 'direct' },
        { label: 'ORD12347', type: 'direct' },
        { label: 'Ask something else', type: 'text', icon: '💬' },
        { label: 'Back to main menu', type: 'back' }
      ],
      'DELIVERY_TRACKING': [
        { label: 'ORD12345', type: 'direct' },
        { label: 'ORD12346', type: 'direct' },
        { label: 'Ask something else', type: 'text', icon: '💬' },
        { label: 'Back to main menu', type: 'back' }
      ],
      'RETURN_REQUEST': [
        { label: 'ORD12345', type: 'direct' },
        { label: 'ORD12346', type: 'direct' },
        { label: 'Ask something else', type: 'text', icon: '💬' },
        { label: 'Back to main menu', type: 'back' }
      ],
      'DAMAGED_ITEM': [
        { label: 'ORD12346', type: 'direct' },
        { label: 'Report damage', type: 'text' },
        { label: 'Ask something else', type: 'text', icon: '💬' },
        { label: 'Back to main menu', type: 'back' }
      ],
      'MISSING_ITEM': [
        { label: 'File claim', type: 'text' },
        { label: 'Check details', type: 'text' },
        { label: 'Ask something else', type: 'text', icon: '💬' },
        { label: 'Back to main menu', type: 'back' }
      ],
      'CANCEL_ORDER': [
        { label: 'ORD12347', type: 'direct' },
        { label: 'Check status', type: 'text' },
        { label: 'Ask something else', type: 'text', icon: '💬' },
        { label: 'Back to main menu', type: 'back' }
      ],
      'DELIVERY_DELAY': [
        { label: 'ORD12345', type: 'direct' },
        { label: 'Get refund', type: 'text' },
        { label: 'Ask something else', type: 'text', icon: '💬' },
        { label: 'Back to main menu', type: 'back' }
      ],
      'TAX_CUSTOMS': [
        { label: 'USA', type: 'text' },
        { label: 'UK', type: 'text' },
        { label: 'Japan', type: 'text' },
        { label: 'Ask something else', type: 'text', icon: '💬' },
        { label: 'Back to main menu', type: 'back' }
      ],
      'INTERNATIONAL_SHIPPING': [
        { label: 'Where is my order?', type: 'text' },
        { label: 'Customs info', type: 'text' },
        { label: 'Ask something else', type: 'text', icon: '💬' },
        { label: 'Back to main menu', type: 'back' }
      ],
      'PERISHABLE_PRODUCT': [
        { label: 'Storage instructions', type: 'text' },
        { label: 'Return policy', type: 'text' },
        { label: 'Ask something else', type: 'text', icon: '💬' },
        { label: 'Back to main menu', type: 'back' }
      ],
      'PAYMENT_ISSUE': [
        { label: 'Charged twice', type: 'text' },
        { label: 'Payment failed', type: 'text' },
        { label: 'Ask something else', type: 'text', icon: '💬' },
        { label: 'Back to main menu', type: 'back' }
      ],
      'OTHER': [
        { label: 'Ask another question', type: 'text' },
        { label: 'Ask something else', type: 'text', icon: '💬' },
        { label: 'Back to main menu', type: 'back' }
      ]
    };

    return contextMap[intentCode] || [
      { label: 'Continue', type: 'text' },
      { label: 'Ask something else', type: 'text', icon: '💬' },
        { label: 'Back to main menu', type: 'back' }
    ];
  };

  const handleIntentSelect = async (intentCode) => {
    setCurrentIntent(intentCode);
    setSuggestions([]);

    try {
      const response = await fetch(`${API_URL}/api/support-intent`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ intent: intentCode })
      });

      const data = await response.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.initial_message }]);

      if (intentCode === 'OTHER') {
        setSuggestions([]);
      } else {
        setSuggestions(getContextSuggestions(intentCode));
      }
    } catch (error) {
      console.error('Intent error:', error);
      setSuggestions(initialSuggestions);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_URL}/api/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Upload failed');

      const data = await response.json();
      setUploadedFile(file.name);
      setFileContext(data.file_context);
      setFileType(data.file_type);
    } catch (error) {
      alert(`Upload failed: ${error.message}`);
    }
  };

  const handleSendMessage = async (messageText, isDirectSend = false) => {
    const userMessage = messageText || input;
    if (!userMessage.trim() || loading) return;

    if (!isDirectSend) {
      setInput('');
    }

    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setSuggestions([]);
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          model: selectedModel,
          history: messages,
          file_context: fileContext,
          file_type: fileType,
          intent: currentIntent,
        }),
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullResponse = '';
      let isFirstChunk = true;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        fullResponse += chunk;

        if (isFirstChunk) {
          setMessages(prev => [...prev, { role: 'assistant', content: fullResponse }]);
          isFirstChunk = false;
        } else {
          setMessages(prev => {
            const updated = [...prev];
            updated[updated.length - 1].content = fullResponse;
            return updated;
          });
        }
      }

      if (currentIntent && currentIntent !== 'OTHER') {
        setSuggestions(getContextSuggestions(currentIntent));
      }
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `❌ Error: ${error.message}`
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestionAction = (suggestion) => {
    if (suggestion.type === 'back') {
      handleBackToMenu();
    } else if (suggestion.type === 'direct') {
      handleSendMessage(suggestion.label, true);
    } else if (suggestion.type === 'intent') {
      handleIntentSelect(suggestion.code);
    } else if (suggestion.type === 'text') {
      // Show text input box for text suggestions
      setShowTextInput(true);
      setInput(suggestion.label);
    }
  };

  const handleBackToMenu = () => {
    setCurrentIntent(null);
    setShowTextInput(false);
    setInput('');
    setMessages([
      { role: 'assistant', content: 'Hello! How can we help you today? Click any option below or type your question.' }
    ]);
    setSuggestions(initialSuggestions);
  };

  const handleFormSubmit = (e) => {
    e.preventDefault();
    handleSendMessage(input, false);
  };

  const messagesEndRef = React.useRef(null);
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, suggestions]);

  return (
    <div className="app">
      <header className="header">
        <h1>QuickCommerce Support</h1>
        <select 
          value={selectedModel} 
          onChange={(e) => setSelectedModel(e.target.value)}
          className="model-select"
        >
          {Object.entries(models).map(([key, label]) => (
            <option key={key} value={key}>{label}</option>
          ))}
        </select>
      </header>

      <main className="chat-container">
        <div className="messages">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message message-${msg.role}`}>
              <div className="message-content">
                {msg.content}
              </div>
            </div>
          ))}

          {!loading && suggestions.length > 0 && (
            <div className="suggestions-container">
              <div className="suggestions-label">Suggested actions:</div>
              <div className="suggestions-grid">
                {suggestions.map((suggestion, idx) => (
                  <button
                    key={idx}
                    className="suggestion-button"
                    onClick={() => handleSuggestionAction(suggestion)}
                    disabled={loading}
                  >
                    {suggestion.icon && <span className="suggestion-icon">{suggestion.icon}</span>}
                    {suggestion.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {loading && (
            <div className="message message-assistant">
              <div className="message-content">
                <span className="typing-indicator">● ● ●</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </main>

      {(currentIntent === 'OTHER' || currentIntent === null || showTextInput) && (
        <footer className="footer">
          <form onSubmit={handleFormSubmit} className="input-form">
            <label className="file-upload">
              <input 
                type="file" 
                onChange={handleFileUpload}
                accept=".pdf,.png,.jpg,.jpeg,.txt,.csv,.docx"
              />
              <span className="file-button">+</span>
            </label>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your question or order ID..."
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
          
          {uploadedFile && (
            <div className="file-indicator">
              📎 {uploadedFile}
              <button 
                onClick={() => {
                  setUploadedFile(null);
                  setFileContext(null);
                  setFileType(null);
                }}
                className="clear-file"
                type="button"
              >
                ✕
              </button>
            </div>
          )}
        </footer>
      )}
    </div>
  );
}

export default App;