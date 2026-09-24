import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { inventoryApi } from '../services/api';
import type { SKU } from '../types';
import '../styles/Dashboard.css';

export default function Dashboard() {
  const navigate = useNavigate();
  const [inventory, setInventory] = useState<SKU[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'critical' | 'high' | 'medium' | 'low'>('all');

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

      <div className="stats-grid">
        <div className="stat-card">
          <h3>Total SKUs</h3>
          <p className="stat-value">{inventory.length}</p>
        </div>
        <div className="stat-card critical">
          <h3>Critical Risk</h3>
          <p className="stat-value">{criticalCount}</p>
        </div>
        <div className="stat-card high">
          <h3>High Risk</h3>
          <p className="stat-value">{highCount}</p>
        </div>
        <div className="stat-card">
          <h3>Total Stock</h3>
          <p className="stat-value">
            {inventory.reduce((sum, sku) => sum + sku.current_stock, 0).toLocaleString()}
          </p>
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
