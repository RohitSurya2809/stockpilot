import { useState } from 'react';
import { simulationApi } from '../services/api';
import type { SimulationResult } from '../types';
import '../styles/Simulation.css';

export default function Simulation() {
  const [skuId, setSkuId] = useState('SKU-004');
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRunSimulation = async () => {
    if (!skuId.trim()) {
      setError('Please enter a SKU ID');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const data = await simulationApi.run(skuId);
      setResult(data);
    } catch (err) {
      setError('Failed to run simulation');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="simulation-page">
      <h2>Baseline Comparison</h2>
      <p className="subtitle">
        Compare Fixed Threshold strategy vs StockPilot Adaptive strategy
      </p>

      <div className="simulation-input-section">
        <div className="input-group">
          <label htmlFor="sku-sim-input">SKU ID:</label>
          <input
            id="sku-sim-input"
            type="text"
            value={skuId}
            onChange={(e) => setSkuId(e.target.value)}
            placeholder="Enter SKU ID (e.g., SKU-004)"
            onKeyDown={(e) => e.key === 'Enter' && handleRunSimulation()}
          />
          <button
            onClick={handleRunSimulation}
            disabled={loading}
            className="btn-primary"
          >
            {loading ? 'Running Simulation...' : 'Run Simulation'}
          </button>
        </div>

        <div className="quick-links">
          <p>Quick Select:</p>
          <button onClick={() => setSkuId('SKU-004')} className="quick-btn">
            SKU-004 (Demo - Demand Spike)
          </button>
          <button onClick={() => setSkuId('SKU-002')} className="quick-btn">
            SKU-002 (Increasing Trend)
          </button>
          <button onClick={() => setSkuId('SKU-006')} className="quick-btn">
            SKU-006 (High Volatility)
          </button>
        </div>
      </div>

      {error && (
        <div className="error-banner">
          <p>{error}</p>
        </div>
      )}

      {result && (
        <div className="simulation-results">
          <div className="result-header">
            <h3>Simulation Results: {result.sku_id}</h3>
            <span className="sim-days">{result.simulation_days} days simulated</span>
          </div>

          <div className="comparison-grid">
            {/* Fixed Threshold */}
            <div className="strategy-card fixed">
              <h4>Fixed Threshold Strategy</h4>
              <p className="strategy-desc">Traditional static reorder point</p>

              <div className="metrics">
                <div className="metric">
                  <span className="metric-label">Stockouts:</span>
                  <span className="metric-value large">
                    {result.fixed_threshold.stockouts}
                  </span>
                </div>
                <div className="metric">
                  <span className="metric-label">Service Level:</span>
                  <span className="metric-value">
                    {(result.fixed_threshold.service_level * 100).toFixed(2)}%
                  </span>
                </div>
                <div className="metric">
                  <span className="metric-label">Avg Inventory:</span>
                  <span className="metric-value">
                    {result.fixed_threshold.average_inventory.toFixed(0)} units
                  </span>
                </div>
                <div className="metric">
                  <span className="metric-label">Orders Placed:</span>
                  <span className="metric-value">
                    {result.fixed_threshold.orders_placed}
                  </span>
                </div>
              </div>
            </div>

            {/* Adaptive Strategy */}
            <div className="strategy-card adaptive">
              <h4>StockPilot Adaptive</h4>
              <p className="strategy-desc">Intelligent dynamic reorder point</p>

              <div className="metrics">
                <div className="metric">
                  <span className="metric-label">Stockouts:</span>
                  <span className="metric-value large success">
                    {result.adaptive.stockouts}
                  </span>
                </div>
                <div className="metric">
                  <span className="metric-label">Service Level:</span>
                  <span className="metric-value">
                    {(result.adaptive.service_level * 100).toFixed(2)}%
                  </span>
                </div>
                <div className="metric">
                  <span className="metric-label">Avg Inventory:</span>
                  <span className="metric-value">
                    {result.adaptive.average_inventory.toFixed(0)} units
                  </span>
                </div>
                <div className="metric">
                  <span className="metric-label">Orders Placed:</span>
                  <span className="metric-value">
                    {result.adaptive.orders_placed}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Improvement Metrics */}
          <div className="improvement-section">
            <h4>Improvement Summary</h4>
            <div className="improvement-grid">
              <div className="improvement-card">
                <span className="improvement-label">Stockout Reduction:</span>
                <span className="improvement-value success">
                  {result.improvement.stockout_reduction > 0
                    ? `-${result.improvement.stockout_reduction}`
                    : result.improvement.stockout_reduction}
                </span>
              </div>
              <div className="improvement-card">
                <span className="improvement-label">Service Level Improvement:</span>
                <span className="improvement-value success">
                  +{(result.improvement.service_level_improvement * 100).toFixed(2)}%
                </span>
              </div>
              <div className="improvement-card">
                <span className="improvement-label">Result:</span>
                <span className="improvement-value bold">
                  {result.adaptive.stockouts === 0 && result.fixed_threshold.stockouts > 0
                    ? '100% Stockout Elimination'
                    : `${Math.abs(
                        ((result.adaptive.stockouts - result.fixed_threshold.stockouts) /
                          (result.fixed_threshold.stockouts || 1)) *
                          100
                      ).toFixed(0)}% Improvement`}
                </span>
              </div>
            </div>
          </div>

          {/* Insights */}
          <div className="insights-section">
            <h4>Key Insights</h4>
            <ul className="insights-list">
              {result.fixed_threshold.stockouts > result.adaptive.stockouts && (
                <li className="insight success">
                  <strong>Success:</strong> StockPilot prevented{' '}
                  {result.fixed_threshold.stockouts - result.adaptive.stockouts} stockout(s)
                  during the simulation period.
                </li>
              )}
              {result.adaptive.service_level > result.fixed_threshold.service_level && (
                <li className="insight success">
                  <strong>Improved Service Level:</strong> StockPilot achieved{' '}
                  {(result.adaptive.service_level * 100).toFixed(2)}% service level vs{' '}
                  {(result.fixed_threshold.service_level * 100).toFixed(2)}% for fixed threshold.
                </li>
              )}
              {result.adaptive.orders_placed === result.fixed_threshold.orders_placed && (
                <li className="insight info">
                  <strong>Same Efficiency:</strong> Both strategies placed{' '}
                  {result.adaptive.orders_placed} orders - StockPilot doesn't order more
                  frequently, it orders smarter.
                </li>
              )}
              {result.adaptive.average_inventory > result.fixed_threshold.average_inventory && (
                <li className="insight info">
                  <strong>Safety Stock:</strong> StockPilot maintains{' '}
                  {(
                    ((result.adaptive.average_inventory - result.fixed_threshold.average_inventory) /
                      result.fixed_threshold.average_inventory) *
                    100
                  ).toFixed(0)}
                  % higher average inventory as safety buffer - preventing stockouts without
                  excessive reordering.
                </li>
              )}
            </ul>
          </div>

          <div className="simulation-note">
            <p>
              <strong>Note:</strong> This simulation uses actual historical demand data to compare
              both strategies under identical conditions. The results demonstrate StockPilot's
              ability to adapt to demand changes and prevent stockouts proactively.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
