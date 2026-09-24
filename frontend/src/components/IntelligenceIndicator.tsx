import { useEffect, useState } from 'react';
import '../styles/IntelligenceIndicator.css';

interface Props {
  skuId: string;
  currentStock: number;
  reorderPoint: number;
  daysUntilStockout: number | null;
  riskLevel: string | null;
}

export default function IntelligenceIndicator({
  skuId,
  currentStock,
  reorderPoint,
  daysUntilStockout,
  riskLevel
}: Props) {
  const [recommendation, setRecommendation] = useState<string>('');
  const [analyzing, setAnalyzing] = useState(true);

  useEffect(() => {
    // Simulate intelligence calculation
    setTimeout(() => {
      const below = currentStock < reorderPoint;
      const critical = (daysUntilStockout || 999) < 7;

      if (critical && below) {
        setRecommendation('🚨 AGENT ALERT: Order NOW - Stockout imminent!');
      } else if (below) {
        setRecommendation('⚠️ AGENT: Reorder recommended - Below dynamic ROP');
      } else if (riskLevel === 'critical') {
        setRecommendation('🔍 FORECAST: High risk detected - Monitor closely');
      } else {
        setRecommendation('✅ ANALYSIS: Inventory sufficient');
      }
      setAnalyzing(false);
    }, 300);
  }, [skuId, currentStock, reorderPoint, daysUntilStockout, riskLevel]);

  const below = currentStock < reorderPoint;
  const diff = Math.abs(currentStock - reorderPoint);
  const diffPercent = ((diff / reorderPoint) * 100).toFixed(0);

  return (
    <div className="intelligence-indicator">
      <div className="intel-header">
        <span className="intel-icon">🤖</span>
        <span className="intel-title">Live Intelligence</span>
        {analyzing && <span className="analyzing-dot"></span>}
      </div>

      <div className="intel-body">
        <div className="intel-recommendation">
          {recommendation}
        </div>

        <div className="intel-calculation">
          <div className="calc-item">
            <span className="calc-label">Current Stock:</span>
            <span className="calc-value">{currentStock}</span>
          </div>
          <div className="calc-item">
            <span className="calc-label">Dynamic ROP:</span>
            <span className="calc-value bold">{reorderPoint}</span>
          </div>
          <div className="calc-item">
            <span className="calc-label">Difference:</span>
            <span className={`calc-value ${below ? 'danger' : 'success'}`}>
              {below ? '-' : '+'}{diff} ({below ? '-' : '+'}{diffPercent}%)
            </span>
          </div>
        </div>

        {daysUntilStockout && (
          <div className="intel-prediction">
            <span className="prediction-label">📊 Forecast:</span>
            <span className="prediction-value">
              Stockout in {daysUntilStockout.toFixed(1)} days
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
