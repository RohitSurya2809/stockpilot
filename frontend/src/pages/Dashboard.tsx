import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { inventoryApi, n8nApi } from '../services/api';
import type { SKU } from '../types';
import '../styles/Dashboard.css';

export default function Dashboard() {
  const navigate = useNavigate();
  const [inventory, setInventory] = useState<SKU[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'critical' | 'high' | 'medium' | 'low'>('all');
  const [n8nStatus, setN8nStatus] = useState<string | null>(null);
  const [n8nLoading, setN8nLoading] = useState(false);

  useEffect(() => {
    loadInventory();
  }, []);

  const loadInventory = async () => {
    try {
      setLoading(true);
      const data = await inventoryApi.getAll();
      setInventory(data);
      setError(null);
    } catch (err) {
      setError('Failed to load inventory data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getRiskBadgeClass = (riskLevel: string | null) => {
    if (!riskLevel) return 'risk-badge unknown';
    return `risk-badge ${riskLevel.toLowerCase()}`;
  };

  const getTrendIcon = (trend: string | null) => {
    if (!trend) return '—';
    if (trend.toLowerCase().includes('increas')) return '↗';
    if (trend.toLowerCase().includes('decreas')) return '↘';
    return '→';
  };

  const filteredInventory = inventory.filter((sku) => {
    if (filter === 'all') return true;
    return sku.risk_level?.toLowerCase() === filter;
  });

  const criticalCount = inventory.filter((s) => s.risk_level === 'critical').length;
  const highCount = inventory.filter((s) => s.risk_level === 'high').length;

  const handleCheckReorder = async () => {
    try {
      setN8nLoading(true);
      setN8nStatus(null);
      const data = await n8nApi.checkReorder();
      if (data.reorder_needed > 0) {
        const skuList = data.alerts.map((a: any) => a.sku_id).join(', ');
        setN8nStatus(`Found ${data.reorder_needed} SKUs needing reorder: ${skuList}. Checked ${data.total_skus_checked} total.`);
      } else {
        setN8nStatus(`All ${data.total_skus_checked} SKUs checked - no reorders needed.`);
      }
    } catch (err) {
      setN8nStatus('Failed to check reorder status');
      console.error(err);
    } finally {
      setN8nLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading inventory...</div>;
  }

  if (error) {
    return (
      <div className="error-container">
        <p className="error">{error}</p>
        <button onClick={loadInventory} className="retry-btn">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h2>Inventory Dashboard</h2>
        <button onClick={loadInventory} className="refresh-btn">
          Refresh
        </button>
      </div>

      {/* StockPilot Intelligence Section */}
      <div className="intelligence-section">
        <div className="section-header">
          <div className="section-title">
            <span className="intelligence-icon">🤖</span>
            <h3>StockPilot Intelligence</h3>
          </div>
          <span className="section-badge">ML-Powered Insights</span>
        </div>
        <div className="stats-grid intelligence-grid">
          <div className="stat-card critical">
            <div className="stat-header">
              <span className="stat-icon">🚨</span>
              <h3>Critical Risk</h3>
            </div>
            <p className="stat-value">{criticalCount}</p>
            <p className="stat-detail">Immediate attention needed</p>
          </div>
          <div className="stat-card high">
            <div className="stat-header">
              <span className="stat-icon">⚠️</span>
              <h3>High Risk</h3>
            </div>
            <p className="stat-value">{highCount}</p>
            <p className="stat-detail">Monitor closely</p>
          </div>
          <div className="stat-card intelligence">
            <div className="stat-header">
              <span className="stat-icon">📊</span>
              <h3>ML Forecast Active</h3>
            </div>
            <p className="stat-value">{inventory.length}</p>
            <p className="stat-detail">RandomForestRegressor</p>
          </div>
          <div className="stat-card intelligence">
            <div className="stat-header">
              <span className="stat-icon">🎯</span>
              <h3>Dynamic ROP</h3>
            </div>
            <p className="stat-value">
              {inventory.filter(s => s.current_stock < s.reorder_point).length}
            </p>
            <p className="stat-detail">Below reorder point</p>
          </div>
        </div>
        <div className="n8n-actions">
          <button
            className="btn-n8n"
            onClick={handleCheckReorder}
            disabled={n8nLoading}
          >
            {n8nLoading ? 'Checking...' : 'Run Reorder Check (n8n Workflow 3)'}
          </button>
          {n8nStatus && (
            <div className="n8n-status">{n8nStatus}</div>
          )}
        </div>
      </div>

      {/* Operational Data Section */}
      <div className="operational-section">
        <div className="section-header">
          <div className="section-title">
            <span className="operational-icon">📦</span>
            <h3>Operational Data</h3>
          </div>
          <span className="section-badge operational">Database View</span>
        </div>
        <div className="stats-grid operational-grid">
          <div className="stat-card operational">
            <div className="stat-header">
              <h3>Total SKUs</h3>
            </div>
            <p className="stat-value">{inventory.length}</p>
            <p className="stat-detail">Products tracked</p>
          </div>
          <div className="stat-card operational">
            <div className="stat-header">
              <h3>Total Stock</h3>
            </div>
            <p className="stat-value">
              {inventory.reduce((sum, sku) => sum + sku.current_stock, 0).toLocaleString()}
            </p>
            <p className="stat-detail">Units in inventory</p>
          </div>
          <div className="stat-card operational">
            <div className="stat-header">
              <h3>Avg Stock Level</h3>
            </div>
            <p className="stat-value">
              {inventory.length > 0
                ? Math.round(inventory.reduce((sum, sku) => sum + sku.current_stock, 0) / inventory.length)
                : 0}
            </p>
            <p className="stat-detail">Units per SKU</p>
          </div>
          <div className="stat-card operational">
            <div className="stat-header">
              <h3>Avg Demand</h3>
            </div>
            <p className="stat-value">
              {inventory.length > 0
                ? (inventory.reduce((sum, sku) => sum + sku.recent_daily_demand, 0) / inventory.length).toFixed(1)
                : 0}
            </p>
            <p className="stat-detail">Units/day avg</p>
          </div>
        </div>
      </div>

      <div className="filter-bar">
        <button
          className={filter === 'all' ? 'filter-btn active' : 'filter-btn'}
          onClick={() => setFilter('all')}
        >
          All ({inventory.length})
        </button>
        <button
          className={filter === 'critical' ? 'filter-btn active' : 'filter-btn'}
          onClick={() => setFilter('critical')}
        >
          Critical ({criticalCount})
        </button>
        <button
          className={filter === 'high' ? 'filter-btn active' : 'filter-btn'}
          onClick={() => setFilter('high')}
        >
          High ({highCount})
        </button>
        <button
          className={filter === 'medium' ? 'filter-btn active' : 'filter-btn'}
          onClick={() => setFilter('medium')}
        >
          Medium
        </button>
        <button
          className={filter === 'low' ? 'filter-btn active' : 'filter-btn'}
          onClick={() => setFilter('low')}
        >
          Low
        </button>
      </div>

      <div className="inventory-grid">
        {filteredInventory.map((sku) => (
          <div key={sku.sku_id} className="inventory-card">
            <div className="card-header">
              <h3>{sku.product_name}</h3>
              <span className={getRiskBadgeClass(sku.risk_level)}>
                {sku.risk_level || 'Unknown'}
              </span>
            </div>

            <div className="card-body">
              <div className="info-row">
                <span className="label">SKU:</span>
                <span className="value">{sku.sku_id}</span>
              </div>
              <div className="info-row">
                <span className="label">Category:</span>
                <span className="value">{sku.category}</span>
              </div>
              <div className="info-row">
                <span className="label">Current Stock:</span>
                <span className="value bold">{sku.current_stock} units</span>
              </div>
              <div className="info-row">
                <span className="label">Reorder Point:</span>
                <span className="value">{sku.reorder_point} units</span>
              </div>
              <div className="info-row">
                <span className="label">Demand (avg/day):</span>
                <span className="value">{sku.recent_daily_demand.toFixed(1)} units</span>
              </div>
              {sku.days_until_stockout !== null && (
                <div className="info-row">
                  <span className="label">Days until stockout:</span>
                  <span className="value">{sku.days_until_stockout.toFixed(1)} days</span>
                </div>
              )}
              <div className="info-row">
                <span className="label">Trend:</span>
                <span className="value">
                  {getTrendIcon(sku.demand_trend)} {sku.demand_trend || 'Unknown'}
                </span>
              </div>
              <div className="info-row">
                <span className="label">Supplier:</span>
                <span className="value">{sku.supplier_name}</span>
              </div>
              <div className="info-row">
                <span className="label">Lead Time:</span>
                <span className="value">{sku.supplier_lead_time} days</span>
              </div>
            </div>

            <div className="card-footer">
              <button
                className="btn-secondary"
                onClick={() => navigate(`/analysis?sku=${sku.sku_id}`)}
              >
                View Details
              </button>
              <button
                className="btn-primary"
                onClick={() => navigate(`/analysis?sku=${sku.sku_id}`)}
              >
                Analyze
              </button>
            </div>
          </div>
        ))}
      </div>

      {filteredInventory.length === 0 && (
        <div className="empty-state">
          <p>No inventory items match the selected filter.</p>
        </div>
      )}
    </div>
  );
}
