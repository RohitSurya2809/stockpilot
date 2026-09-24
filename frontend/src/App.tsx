import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
import Dashboard from './pages/Dashboard';
import Analysis from './pages/Analysis';
import Simulation from './pages/Simulation';
import AssistantPanel from './components/AssistantPanel';
import { healthCheck } from './services/api';
import './styles/App.css';

function AppContent() {
  const location = useLocation();
  const page = location.pathname === '/' ? 'dashboard'
    : location.pathname.replace('/', '');
  const [systemStatus, setSystemStatus] = useState<'loading' | 'online' | 'offline'>('loading');

  useEffect(() => {
    healthCheck()
      .then(() => setSystemStatus('online'))
      .catch(() => setSystemStatus('offline'));
  }, []);

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-top">
          <div className="header-brand">
            <div className="brand-logo">SP</div>
            <div>
              <h1>StockPilot</h1>
              <p className="tagline">AI-Powered Inventory Intelligence</p>
            </div>
          </div>
          <div className="header-status">
            <div className={`status-indicator ${systemStatus}`}>
              <span className="status-dot"></span>
              <span className="status-text">
                {systemStatus === 'online' ? 'System Online' : systemStatus === 'loading' ? 'Connecting...' : 'Offline'}
              </span>
            </div>
            <div className="tech-badges">
              <span className="tech-badge">ML: RandomForest</span>
              <span className="tech-badge">LLM: Qwen3</span>
              <span className="tech-badge">n8n: 3 Workflows</span>
            </div>
          </div>
        </div>
        <nav className="main-nav">
          <Link to="/" className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}>
            <span className="nav-icon">||</span> Dashboard
          </Link>
          <Link to="/analysis" className={`nav-link ${location.pathname === '/analysis' ? 'active' : ''}`}>
            <span className="nav-icon">~</span> Analysis
          </Link>
          <Link to="/simulation" className={`nav-link ${location.pathname === '/simulation' ? 'active' : ''}`}>
            <span className="nav-icon">&lt;&gt;</span> Simulation
          </Link>
        </nav>
      </header>

      <main className="app-main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/analysis" element={<Analysis />} />
          <Route path="/simulation" element={<Simulation />} />
        </Routes>
      </main>

      <footer className="app-footer">
        <div className="footer-content">
          <p>StockPilot - Hack the Horizon 2.0</p>
          <p className="footer-tech">FastAPI + PostgreSQL + sklearn + Ollama + n8n + React</p>
        </div>
      </footer>

      <AssistantPanel page={page} />
    </div>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;
