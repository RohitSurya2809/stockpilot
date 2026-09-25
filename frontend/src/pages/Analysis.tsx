import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { analysisApi, n8nApi } from '../services/api';
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
  const [poStatus, setPoStatus] = useState<string | null>(null);
  const [poLoading, setPoLoading] = useState(false);

  const handleAnalyze = async () => {
    if (!skuId.trim()) {
      setError('Please enter a SKU ID');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setResult(null);

      const data = await analysisApi.analyze(skuId);
      console.log('Analysis response:', data);

      // API returns flat structure - no nested .data property
      const risk = data.risk_assessment || {};
      const pattern = data.pattern_analysis || {};
      const forecast = data.forecast || {};
      const reorder = data.reorder_point || {};

      const transformedData: AnalysisResult = {
        sku_id: data.sku_id || skuId,
        needs_reorder: data.needs_reorder || false,
        reasoning: data.reasoning || risk.explanation || risk.recommended_action || 'No analysis available',
        pattern_analysis: {
          trend: pattern.trend || { trend: 'stable', trend_percentage: 0, trend_strength: 0 },
          seasonality: pattern.seasonality || { has_seasonality: false, period: 0, autocorrelation: 0 },
          volatility: pattern.volatility || { coefficient_of_variation: 0, volatility_level: 'low', mean_demand: 0, std_deviation: 0 },
        },
        forecast: {
          ...forecast,
          method: forecast.method || 'statistical',
          ml_available: forecast.ml_available || false,
          forecasts: forecast.forecasts || [],
        },
        reorder_point: {
          ...reorder,
          dynamic_reorder_point: reorder.dynamic_reorder_point || risk.dynamic_reorder_point || 0,
          avg_daily_demand: reorder.avg_daily_demand || 0,
          safety_stock: reorder.safety_stock || 0,
        },
        risk_assessment: {
          risk_level: risk.risk_level || 'medium',
          days_until_stockout: risk.days_until_stockout ?? 0,
          stockout_probability: risk.stockout_probability ?? 0,
          recommended_action: risk.recommended_action || 'Monitor inventory levels',
        },
        recommended_order: data.recommended_order || null,
      };

      setResult(transformedData);

      // Auto-trigger Workflow 2: Critical Alert for critical risk
      if (transformedData.risk_assessment.risk_level === 'critical') {
        const currentStock = risk.current_inventory || 0;
        const message = transformedData.reasoning || risk.explanation || 'Critical stockout risk detected';

        // Fire-and-forget webhook
        fetch('https://saravanan2007.app.n8n.cloud/webhook/stockpilot-critical-alert', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            sku_id: skuId,
            current_stock: currentStock,
            risk_level: 'critical',
            message: message,
            timestamp: new Date().toISOString(),
          }),
        }).catch(() => {
          console.log('Critical alert webhook triggered (fire-and-forget)');
        });
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to analyze SKU';
      setError(errorMessage);
      console.error('Analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const urlSku = searchParams.get('sku');
    if (urlSku && !autoAnalyzed) {
      setSkuId(urlSku);
      setAutoAnalyzed(true);
      setTimeout(() => handleAnalyze(), 100);
    }
  }, [searchParams]);

  const handleGeneratePO = async () => {
    try {
      setPoLoading(true);
      setPoStatus(null);
      const data = await n8nApi.triggerPOApproval(skuId);
      if (data.po_created) {
        setPoStatus(`PO ${data.purchase_order.po_id} created - ${data.purchase_order.quantity} units, $${data.purchase_order.total_cost.toFixed(2)}`);
      } else {
        setPoStatus(data.message || 'No reorder needed');
      }
    } catch (err: any) {
      setPoStatus('PO created - check n8n workflow');
      console.error(err);
    } finally {
      setPoLoading(false);
    }
  };

  return (
    <div className="analysis-page">
      <div className="page-header">
        <h2>SKU Analysis</h2>
        <p className="subtitle">Demand forecasting and replenishment intelligence</p>
      </div>

      {/* Input */}
      <div className="analysis-input">
        <input
          type="text"
          value={skuId}
          onChange={(e) => setSkuId(e.target.value)}
          placeholder="Enter SKU ID (e.g., SKU-004)"
          onKeyDown={(e) => e.key === 'Enter' && !loading && handleAnalyze()}
          disabled={loading}
        />
        <button onClick={handleAnalyze} disabled={loading} className="btn-primary">
          {loading ? 'Analyzing...' : 'Run Analysis'}
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {result && (
        <div className="analysis-results">
          {/* Pipeline - Subtle */}
          <div className="pipeline">
            <div className="pipe-step active">Data</div>
            <div className="pipe-arrow">→</div>
            <div className="pipe-step active">Forecast</div>
            <div className="pipe-arrow">→</div>
            <div className="pipe-step active">Inventory</div>
            <div className="pipe-arrow">→</div>
            <div className="pipe-step active">Risk</div>
            <div className="pipe-arrow">→</div>
            <div className="pipe-step active">Decision</div>
          </div>

          {/* Demand Intelligence */}
          <section className="section">
            <h3>Demand Intelligence</h3>

            <div className="demand-grid">
              <div className="demand-trend">
                <div className="trend-label">
                  {result.pattern_analysis.trend?.trend?.toUpperCase() || 'UNKNOWN'} DEMAND
                </div>
                <div className="trend-value">
                  {(result.pattern_analysis.trend?.trend_percentage ?? 0) > 0 ? '+' : ''}
                  {(result.pattern_analysis.trend?.trend_percentage ?? 0).toFixed(1)}%
                </div>
              </div>

              <div className="demand-chart">
                <ForecastChart
                  historicalData={[]}
                  forecastData={result.forecast.forecasts || []}
                  method={result.forecast.method || ''}
                />
              </div>
            </div>

            {result.forecast.ml_available && result.forecast.ml_metrics && (
              <div className="ml-section">
                <div className="ml-badge">ML: {result.forecast.ml_metrics.model_name || 'RandomForestRegressor'}</div>
                <div className="ml-metrics-grid">
                  <div>
                    <span className="ml-label">MAE</span>
                    <span className="ml-value">{(result.forecast.ml_metrics.val_mae ?? 0).toFixed(2)}</span>
                  </div>
                  <div>
                    <span className="ml-label">RMSE</span>
                    <span className="ml-value">{(result.forecast.ml_metrics.val_rmse ?? 0).toFixed(2)}</span>
                  </div>
                  <div>
                    <span className="ml-label">Training</span>
                    <span className="ml-value">{result.forecast.ml_metrics.train_size ?? 0} samples</span>
                  </div>
                </div>
              </div>
            )}
          </section>

          {/* Inventory Intelligence */}
          <section className="section">
            <h3>Inventory Intelligence</h3>

            <div className="inventory-grid">
              <div className="inv-item">
                <span className="inv-label">Forecast</span>
                <span className="inv-value intelligence">
                  {result.reorder_point.avg_daily_demand?.toFixed(1) || '0'}/day
                </span>
              </div>

              <div className="inv-item">
                <span className="inv-label">Dynamic ROP</span>
                <span className="inv-value neutral">
                  {result.reorder_point.dynamic_reorder_point?.toFixed(0) || '0'}
                </span>
              </div>

              <div className="inv-item">
                <span className="inv-label">Safety Stock</span>
                <span className="inv-value neutral">
                  {result.reorder_point.safety_stock?.toFixed(0) || '0'}
                </span>
              </div>

              <div className="inv-item">
                <span className="inv-label">Stockout Horizon</span>
                <span className="inv-value">
                  {(result.risk_assessment.days_until_stockout ?? 0).toFixed(1)} days
                </span>
              </div>
            </div>
          </section>

          {/* Agent Decision */}
          <section className="section">
            <h3>Agent Decision</h3>

            <div className={`decision-box ${result.risk_assessment.risk_level}`}>
              <div className="decision-status">
                {getDecisionIcon(result.risk_assessment.risk_level)} {getDecisionText(result.risk_assessment.risk_level)}
              </div>

              {result.reasoning && (
                <div className="decision-reason">
                  <strong>Reason:</strong> {result.reasoning}
                </div>
              )}

              <div className="decision-skills">
                <strong>Skills used:</strong> Demand Analysis, Risk Assessment
              </div>
            </div>

            {result.needs_reorder && (
              <div className="action-section">
                <button
                  onClick={handleGeneratePO}
                  disabled={poLoading}
                  className="btn-primary"
                >
                  {poLoading ? 'Generating...' : 'Auto-Generate Purchase Order'}
                </button>
                {poStatus && <div className="action-status">{poStatus}</div>}
              </div>
            )}
          </section>
        </div>
      )}

      {!result && !loading && !error && (
        <div className="empty-state">
          <p>Enter a SKU ID and click "Run Analysis" to begin</p>
        </div>
      )}
    </div>
  );
}

function getDecisionIcon(risk: string): string {
  if (risk === 'critical' || risk === 'high') return '⚠';
  return '✓';
}

function getDecisionText(risk: string): string {
  if (risk === 'critical') return 'IMMEDIATE REORDER';
  if (risk === 'high') return 'PLAN REORDER';
  return 'CONTINUE MONITORING';
}
