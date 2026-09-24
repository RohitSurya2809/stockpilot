import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Analysis from './pages/Analysis';
import Simulation from './pages/Simulation';
import AssistantPanel from './components/AssistantPanel';
import './styles/App.css';

function AppContent() {
  const location = useLocation();
  const page = location.pathname === '/' ? 'dashboard'
    : location.pathname.replace('/', '');

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1>StockPilot</h1>
          <p className="tagline">Smart Inventory & Procurement Automation</p>
        </div>
        <nav className="main-nav">
          <Link to="/" className="nav-link">Dashboard</Link>
          <Link to="/analysis" className="nav-link">Analysis</Link>
          <Link to="/simulation" className="nav-link">Simulation</Link>
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
        <p>StockPilot - Hack the Horizon 2.0 | Built with Agent/Skill/Tool Architecture</p>
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
