import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { procurementApi } from '../services/api';
import type { AnalysisResult } from '../types';
import ForecastChart from '../components/ForecastChart';
import '../styles/Analysis.css';

export default function Analysis() {
  const [searchParams] = useSearchParams();
  const [skuId, setSkuId] = useState(searchParams.get('sku') || 'SKU-004');
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [autoAnalyzed, setAutoAnalyzed] = useState(false);

  const handleAnalyze = async () => {
    if (!skuId.trim()) {
      setError('Please enter a SKU ID');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const data = await procurementApi.analyze(skuId);
      setResult(data);
    } catch (err) {
      setError('Failed to analyze SKU');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Auto-analyze if SKU comes from URL
  useEffect(() => {
    const urlSku = searchParams.get('sku');
    if (urlSku && !autoAnalyzed) {
      setAutoAnalyzed(true);
      handleAnalyze();
    }
  }, [searchParams, autoAnalyzed]);

  const getRiskClass = (level: string) => {
    return `risk-level ${level.toLowerCase()}`;
  };

  return (
    <div className="analysis-page">
      <h2>SKU Analysis</h2>
      <p className="subtitle">Analyze demand patterns, forecast, and assess risk for any SKU</p>

      <div className="analysis-input-section">
        <div className="input-group">
          <label htmlFor="sku-input">SKU ID:</label>
          <input
            id="sku-input"
            type="text"
            value={skuId}
            onChange={(e) => setSkuId(e.target.value)}
            placeholder="Enter SKU ID (e.g., SKU-004)"
            onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
          />
          <button
            onClick={handleAnalyze}
            disabled={loading}
            className="btn-primary"
          >
            {loading ? 'Analyzing...' : 'Analyze'}
          </button>
        </div>

        <div className="quick-links">
          <p>Quick Select:</p>
          <button onClick={() => setSkuId('SKU-001')} className="quick-btn">SKU-001</button>
          <button onClick={() => setSkuId('SKU-002')} className="quick-btn">SKU-002</button>
          <button onClick={() => setSkuId('SKU-003')} className="quick-btn">SKU-003</button>
          <button onClick={() => setSkuId('SKU-004')} className="quick-btn">SKU-004 (Demo)</button>
        </div>
      </div>

      {error && (
        <div className="error-banner">
          <p>{error}</p>
        </div>
      )}

      {result && (
        <div className="analysis-results">
          <div className="result-header">
            <h3>{result.sku_id} Analysis Results</h3>
            <span className={getRiskClass(result.risk_assessment.risk_level)}>
              {result.risk_assessment.risk_level.toUpperCase()} RISK
            </span>
          </div>

          <div className="reasoning-card">
            <h4>Decision Reasoning</h4>
            <p>{result.reasoning}</p>
            {result.needs_reorder && (
              <div className="action-needed">
                <strong>ACTION REQUIRED:</strong> Reorder recommended
              </div>
            )}
          </div>

          <div className="results-grid">
            {/* Pattern Analysis */}
            <div className="result-card">
              <h4>Demand Pattern</h4>
              <div className="metric-row">
                <span className="metric-label">Trend:</span>
                <span className="metric-value">
                  {result.pattern_analysis.trend.trend.toUpperCase()} (
                  {result.pattern_analysis.trend.trend_percentage.toFixed(1)}%)
                </span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Trend Strength:</span>
                <span className="metric-value">
                  {(result.pattern_analysis.trend.trend_strength * 100).toFixed(0)}%
                </span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Seasonality:</span>
                <span className="metric-value">
                  {result.pattern_analysis.seasonality.has_seasonality ? 'Detected' : 'None'}
                </span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Volatility:</span>
                <span className="metric-value">
                  {result.pattern_analysis.volatility.volatility_level.toUpperCase()}
                </span>
              </div>
            </div>

            {/* Forecast */}
            <div className="result-card">
              <h4>Forecast</h4>

              {/* ML Badge */}
              {result.forecast.ml_available && result.forecast.ml_metrics && (
                <div className="ml-badge-container">
                  <span className="ml-badge">
                    🤖 ML: {result.forecast.ml_metrics.model_name}
                  </span>
                  <span className="ml-source-badge">
                    Source: {result.forecast.source === 'ml' ? 'Machine Learning' : 'Statistical'}
                  </span>
                </div>
              )}

              {!result.forecast.ml_available && (
                <div className="ml-badge-container">
                  <span className="statistical-badge">
                    📊 Statistical Forecast
                  </span>
                </div>
              )}

              <div className="metric-row">
                <span className="metric-label">Method:</span>
                <span className="metric-value">{result.forecast.method}</span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Confidence:</span>
                <span className="metric-value">
                  {(result.forecast.confidence_level * 100).toFixed(0)}%
                </span>
              </div>

              {/* ML Validation Metrics */}
              {result.forecast.ml_available && result.forecast.ml_metrics && (
                <>
                  <div className="metric-row">
                    <span className="metric-label">Validation MAE:</span>
                    <span className="metric-value">
                      {result.forecast.ml_metrics.val_mae.toFixed(2)} units
                    </span>
                  </div>
                  <div className="metric-row">
                    <span className="metric-label">Validation RMSE:</span>
                    <span className="metric-value">
                      {result.forecast.ml_metrics.val_rmse.toFixed(2)} units
                    </span>
                  </div>
                  <div className="metric-row">
                    <span className="metric-label">Training Data:</span>
                    <span className="metric-value">
                      {result.forecast.ml_metrics.train_size} samples
                    </span>
                  </div>
                </>
              )}

              <div className="metric-row">
                <span className="metric-label">Forecast Horizon:</span>
                <span className="metric-value">{result.forecast.forecasts.length} days</span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Avg Forecast:</span>
                <span className="metric-value">
                  {(
                    result.forecast.forecasts.reduce((a, b) => a + b, 0) /
                    result.forecast.forecasts.length
                  ).toFixed(1)}{' '}
                  units/day
                </span>
              </div>
            </div>

            {/* Reorder Point */}
            <div className="result-card">
              <h4>Reorder Point</h4>
              <div className="metric-row">
                <span className="metric-label">Dynamic ROP:</span>
                <span className="metric-value bold">
                  {result.reorder_point.dynamic_reorder_point.toFixed(0)} units
                </span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Expected Demand:</span>
                <span className="metric-value">
                  {result.reorder_point.expected_demand_during_lead_time.toFixed(0)} units
                </span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Safety Stock:</span>
                <span className="metric-value">
                  {result.reorder_point.safety_stock.toFixed(0)} units
                </span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Avg Daily Demand:</span>
                <span className="metric-value">
                  {result.reorder_point.avg_daily_demand.toFixed(1)} units/day
                </span>
              </div>
            </div>

            {/* Risk Assessment */}
            <div className="result-card">
              <h4>Risk Assessment</h4>
              <div className="metric-row">
                <span className="metric-label">Risk Level:</span>
                <span className={`metric-value ${result.risk_assessment.risk_level}`}>
                  {result.risk_assessment.risk_level.toUpperCase()}
                </span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Days Until Stockout:</span>
                <span className="metric-value">
                  {result.risk_assessment.days_until_stockout.toFixed(1)} days
                </span>
              </div>
              <div className="metric-row">
                <span className="metric-label">Stockout Probability:</span>
                <span className="metric-value">
                  {(result.risk_assessment.stockout_probability * 100).toFixed(0)}%
                </span>
              </div>
              <div className="metric-row full-width">
                <span className="metric-label">Recommendation:</span>
                <span className="metric-value">
                  {result.risk_assessment.recommended_action}
                </span>
              </div>
            </div>
          </div>

          {result.recommended_order && (
            <div className="recommended-order-card">
              <h4>Recommended Purchase Order</h4>
              <div className="order-details">
                <div className="order-metric">
                  <span className="label">Quantity:</span>
                  <span className="value">{result.recommended_order.quantity} units</span>
                </div>
                <div className="order-metric">
                  <span className="label">Unit Cost:</span>
                  <span className="value">${result.recommended_order.unit_cost.toFixed(2)}</span>
                </div>
                <div className="order-metric">
                  <span className="label">Total Cost:</span>
                  <span className="value bold">${result.recommended_order.total_cost.toFixed(2)}</span>
                </div>
                <div className="order-metric">
                  <span className="label">Lead Time:</span>
                  <span className="value">{result.recommended_order.lead_time_days} days</span>
                </div>
              </div>
              <button className="btn-primary">Generate Purchase Order</button>
            </div>
          )}

          {/* Forecast Visualization */}
          <ForecastChart
            forecasts={result.forecast.forecasts}
            mlAvailable={result.forecast.ml_available || false}
            confidence={result.forecast.confidence_level}
          />
        </div>
      )}
    </div>
  );
}
