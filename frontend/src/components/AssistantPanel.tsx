import { useState } from 'react';
import api from '../services/api';
import '../styles/AssistantPanel.css';

interface Props {
  page: string;
  pageData?: any;
}

export default function AssistantPanel({ page, pageData }: Props) {
  const [open, setOpen] = useState(false);
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<{ role: string; text: string }[]>([]);
  const [loading, setLoading] = useState(false);

  const handleExplain = async () => {
    setLoading(true);
    setMessages(prev => [...prev, { role: 'user', text: `Explain this ${page} page` }]);
    try {
      const res = await api.post('/assistant/explain', { page, page_data: pageData });
      setMessages(prev => [...prev, { role: 'assistant', text: res.data.response }]);
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', text: 'Assistant is offline. Ollama may not be running.' }]);
    }
    setLoading(false);
  };

  const handleAsk = async () => {
    if (!question.trim()) return;
    const q = question;
    setQuestion('');
    setLoading(true);
    setMessages(prev => [...prev, { role: 'user', text: q }]);
    try {
      const res = await api.post('/assistant/ask', { page, page_data: pageData, question: q });
      setMessages(prev => [...prev, { role: 'assistant', text: res.data.response }]);
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', text: 'Assistant is offline. Ollama may not be running.' }]);
    }
    setLoading(false);
  };

  if (!open) {
    return (
      <button className="assistant-fab" onClick={() => setOpen(true)} title="StockPilot Assistant">
        <span className="fab-icon">AI</span>
      </button>
    );
  }

  return (
    <div className="assistant-panel">
      <div className="assistant-header">
        <div className="assistant-title">
          <span className="assistant-logo">AI</span>
          <span>StockPilot Assistant</span>
        </div>
        <button className="assistant-close" onClick={() => setOpen(false)}>X</button>
      </div>

      <div className="assistant-messages">
        {messages.length === 0 && (
          <div className="assistant-welcome">
            <p>I can explain what you see on this page, answer questions about inventory management, or help you find features.</p>
            <button className="assistant-suggest" onClick={handleExplain}>
              Explain this page
            </button>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`assistant-msg ${msg.role}`}>
            <span className="msg-label">{msg.role === 'user' ? 'You' : 'AI'}</span>
            <p>{msg.text}</p>
          </div>
        ))}
        {loading && (
          <div className="assistant-msg assistant">
            <span className="msg-label">AI</span>
            <p className="typing">Thinking...</p>
          </div>
        )}
      </div>

      <div className="assistant-input">
        <input
          type="text"
          value={question}
          onChange={e => setQuestion(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleAsk()}
          placeholder="Ask about this page..."
          disabled={loading}
        />
        <button onClick={handleAsk} disabled={loading || !question.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}
