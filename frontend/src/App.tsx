import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
import Dashboard from './pages/Dashboard';
import Analysis from './pages/Analysis';
import Simulation from './pages/Simulation';
import AssistantPanel from './components/AssistantPanel';
import { useTheme } from './context/ThemeContext';
import { healthCheck } from './services/api';
import './styles/App.css';

function AppContent() {
  const location = useLocation();
  const page = location.pathname === '/' ? 'dashboard' : location.pathname.replace('/', '');
  const { theme, toggleTheme } = useTheme();
  const [systemStatus, setSystemStatus] = useState<'loading' | 'online' | 'offline'>('loading');

  useEffect(() => {
    healthCheck()
      .then(() => setSystemStatus('online'))
      .catch(() => setSystemStatus('offline'));
  }, []);

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-brand">
          <div className="brand-mark">SP</div>
          <span className="brand-name">StockPilot</span>
        </div>

        <nav className="main-nav">
          <Link to="/" className={location.pathname === '/' ? 'active' : ''}>
            Dashboard
          </Link>
          <Link to="/analysis" className={location.pathname === '/analysis' ? 'active' : ''}>
            Analysis
          </Link>
          <Link to="/simulation" className={location.pathname === '/simulation' ? 'active' : ''}>
            Simulation
          </Link>
        </nav>

        <div className="header-actions">
          <div className={`status-dot ${systemStatus}`}></div>
          <button onClick={toggleTheme} className="theme-toggle" title="Toggle theme">
            {theme === 'light' ? '🌙' : '☀️'}
          </button>
        </div>
      </header>

      <main className="app-main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/analysis" element={<Analysis />} />
          <Route path="/simulation" element={<Simulation />} />
        </Routes>
      </main>

      <AssistantPanel page={page} />
    </div>
  );
}

export default function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}
