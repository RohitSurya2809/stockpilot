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
  const [checkingReorder, setCheckingReorder] = useState(false);
  const [reorderResult, setReorderResult] = useState<string | null>(null);

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

  const handleCheckReorder = async () => {
    try {
      setCheckingReorder(true);
      setReorderResult(null);
      const response = await fetch('http://localhost:8000/api/n8n/check-reorder');
      const data = await response.json();
      setReorderResult(`Checked ${data.total_skus_checked} SKUs - ${data.reorder_needed} need reorder`);

      // Reload inventory to see updated status
      setTimeout(() => loadInventory(), 1000);
    } catch (err) {
      setReorderResult('Failed to check reorder status');
      console.error(err);
    } finally {
      setCheckingReorder(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading inventory...</div>;
  }

  if (error) {
    return (
      <div className="error-container">
        <p className="error">{error}</p>
        <button onClick={loadInventory} className="retry-btn">Retry</button>
      </div>
    );
  }

  // Count SKUs that need analysis (have null risk_level)
  const needsAnalysis = inventory.filter(s => !s.risk_level).length;
  const atRisk = inventory.filter(s => s.risk_level === 'critical' || s.risk_level === 'high').length;
  const lowStock = inventory.filter(s => s.current_stock < s.reorder_point).length;

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div>
          <h2>Inventory Intelligence</h2>
          <p className="subtitle">Real-time demand forecasting and replenishment</p>
        </div>
        <div className="header-actions">
          <button
            onClick={handleCheckReorder}
            disabled={checkingReorder}
            className="btn-primary"
            title="Workflow 3: Check all SKUs for reorder"
          >
            {checkingReorder ? 'Checking...' : 'Check All for Reorder'}
          </button>
        </div>
      </div>

      {reorderResult && (
        <div className="reorder-status">
          {reorderResult}
        </div>
      )}

      {/* Key Metrics */}
      <div className="metrics-row">
        <div className="metric-card">
          <div className="metric-label">SKUs Tracked</div>
          <div className="metric-value">{inventory.length}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Below ROP</div>
          <div className="metric-value">{lowStock}</div>
        </div>
        {atRisk > 0 && (
          <div className="metric-card">
            <div className="metric-label">At Risk</div>
            <div className="metric-value">{atRisk}</div>
          </div>
        )}
      </div>

      {/* SKU List */}
      <div className="sku-list">
        {inventory.map((sku) => {
          const belowROP = sku.current_stock < sku.reorder_point;
          const hasAnalysis = sku.risk_level !== null;

          return (
            <div key={sku.sku_id} className="sku-item">
              <div className="sku-header">
                <div>
                  <h4>{sku.product_name}</h4>
                  <span className="sku-id">{sku.sku_id}</span>
                </div>
                <div className="sku-badges">
                  {belowROP && (
                    <span className="status-badge below-rop">Below ROP</span>
                  )}
                  {hasAnalysis && sku.risk_level && (
                    <span className={`risk-badge badge-${sku.risk_level}`}>
                      {sku.risk_level.toUpperCase()}
                    </span>
                  )}
                </div>
              </div>

              <div className="sku-intelligence">
                {/* Current State */}
                <div className="intel-item">
                  <span className="label">Current Stock</span>
                  <span className="value">{sku.current_stock} units</span>
                </div>

                {/* Demand Forecast */}
                <div className="intel-item">
                  <span className="label">Avg Demand</span>
                  <span className="value intelligence">{sku.recent_daily_demand.toFixed(1)}/day</span>
                </div>

                {/* Reorder Point */}
                <div className="intel-item">
                  <span className="label">Reorder Point</span>
                  <span className="value">{sku.reorder_point}</span>
                </div>

                {/* Days of Stock */}
                <div className="intel-item">
                  <span className="label">Days of Stock</span>
                  <span className="value">
                    {sku.recent_daily_demand > 0
                      ? (sku.current_stock / sku.recent_daily_demand).toFixed(1)
                      : '∞'} days
                  </span>
                </div>

                {/* Risk or Status */}
                {hasAnalysis ? (
                  <>
                    <div className="intel-item">
                      <span className="label">Risk Level</span>
                      <span className={`value ${getRiskClass(sku.risk_level)}`}>
                        {sku.risk_level?.toUpperCase()}
                      </span>
                    </div>
                    {sku.days_until_stockout !== null && (
                      <div className="intel-item">
                        <span className="label">Stockout In</span>
                        <span className="value">{sku.days_until_stockout.toFixed(1)} days</span>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="intel-item full">
                    <span className="label">Status</span>
                    <span className="value neutral">Ready for analysis</span>
                  </div>
                )}
              </div>

              <div className="sku-actions">
                <button
                  className="btn-primary btn-sm"
                  onClick={() => navigate(`/analysis?sku=${sku.sku_id}`)}
                >
                  {hasAnalysis ? 'View Analysis' : 'Run Analysis'}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function getRiskClass(level: string | null): string {
  if (!level) return 'neutral';
  if (level === 'critical') return 'critical';
  if (level === 'high') return 'warning';
  if (level === 'medium') return 'warning';
  if (level === 'low') return 'healthy';
  return 'neutral';
}
