import { useEffect, useRef } from 'react';
import '../styles/ForecastChart.css';

interface Props {
  forecasts: number[];
  historicalData?: number[];
  mlAvailable: boolean;
  confidence: number;
}

export default function ForecastChart({ forecasts, historicalData = [], mlAvailable, confidence }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    // Clear canvas
    ctx.clearRect(0, 0, rect.width, rect.height);

    // Combine historical and forecast data
    const allData = [...historicalData, ...forecasts];
    const maxValue = Math.max(...allData, 0) * 1.1;
    const minValue = 0;

    const padding = 40;
    const chartWidth = rect.width - padding * 2;
    const chartHeight = rect.height - padding * 2;

    // Draw grid
    ctx.strokeStyle = '#e5e7eb';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 5; i++) {
      const y = padding + (chartHeight / 5) * i;
      ctx.beginPath();
      ctx.moveTo(padding, y);
      ctx.lineTo(rect.width - padding, y);
      ctx.stroke();
    }

    // Draw axes
    ctx.strokeStyle = '#6b7280';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(padding, padding);
    ctx.lineTo(padding, rect.height - padding);
    ctx.lineTo(rect.width - padding, rect.height - padding);
    ctx.stroke();

    // Draw Y-axis labels
    ctx.fillStyle = '#6b7280';
    ctx.font = '11px sans-serif';
    ctx.textAlign = 'right';
    for (let i = 0; i <= 5; i++) {
      const value = maxValue - (maxValue / 5) * i;
      const y = padding + (chartHeight / 5) * i;
      ctx.fillText(value.toFixed(0), padding - 10, y + 4);
    }

    // Helper function to get X position
    const getX = (index: number, total: number) => {
      return padding + (chartWidth / (total - 1)) * index;
    };

    // Helper function to get Y position
    const getY = (value: number) => {
      const ratio = (value - minValue) / (maxValue - minValue);
      return rect.height - padding - ratio * chartHeight;
    };

    // Draw historical data if available
    if (historicalData.length > 0) {
      ctx.strokeStyle = '#3b82f6';
      ctx.lineWidth = 2;
      ctx.beginPath();
      historicalData.forEach((value, index) => {
        const x = getX(index, allData.length);
        const y = getY(value);
        if (index === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });
      ctx.stroke();

      // Draw dots for historical data
      ctx.fillStyle = '#3b82f6';
      historicalData.forEach((value, index) => {
        const x = getX(index, allData.length);
        const y = getY(value);
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, Math.PI * 2);
        ctx.fill();
      });
    }

    // Draw forecast data
    const forecastColor = mlAvailable ? '#10b981' : '#f59e0b';
    ctx.strokeStyle = forecastColor;
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();

    const startIndex = historicalData.length > 0 ? historicalData.length - 1 : 0;
    forecasts.forEach((value, index) => {
      const dataIndex = startIndex + index;
      const x = getX(dataIndex, allData.length);
      const y = getY(value);
      if (index === 0 && historicalData.length > 0) {
        const lastHistX = getX(historicalData.length - 1, allData.length);
        const lastHistY = getY(historicalData[historicalData.length - 1]);
        ctx.moveTo(lastHistX, lastHistY);
        ctx.lineTo(x, y);
      } else if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    ctx.stroke();
    ctx.setLineDash([]);

    // Draw dots for forecast
    ctx.fillStyle = forecastColor;
    forecasts.forEach((value, index) => {
      const dataIndex = startIndex + index;
      const x = getX(dataIndex, allData.length);
      const y = getY(value);
      ctx.beginPath();
      ctx.arc(x, y, 3, 0, Math.PI * 2);
      ctx.fill();
    });

    // Draw confidence band for ML forecasts
    if (mlAvailable) {
      ctx.fillStyle = 'rgba(16, 185, 129, 0.1)';
      ctx.beginPath();
      forecasts.forEach((value, index) => {
        const dataIndex = startIndex + index;
        const x = getX(dataIndex, allData.length);
        const upperY = getY(value * (1 + (1 - confidence)));
        if (index === 0) {
          ctx.moveTo(x, upperY);
        } else {
          ctx.lineTo(x, upperY);
        }
      });
      for (let i = forecasts.length - 1; i >= 0; i--) {
        const dataIndex = startIndex + i;
        const x = getX(dataIndex, allData.length);
        const lowerY = getY(forecasts[i] * confidence);
        ctx.lineTo(x, lowerY);
      }
      ctx.closePath();
      ctx.fill();
    }

    // Draw X-axis labels
    ctx.fillStyle = '#6b7280';
    ctx.font = '11px sans-serif';
    ctx.textAlign = 'center';
    const labelInterval = Math.ceil(allData.length / 8);
    allData.forEach((_, index) => {
      if (index % labelInterval === 0 || index === allData.length - 1) {
        const x = getX(index, allData.length);
        const label = index < historicalData.length ? `D-${historicalData.length - index}` : `D+${index - historicalData.length + 1}`;
        ctx.fillText(label, x, rect.height - padding + 20);
      }
    });
  }, [forecasts, historicalData, mlAvailable, confidence]);

  return (
    <div className="forecast-chart-container">
      <div className="chart-header">
        <h4>Demand Forecast Visualization</h4>
        <div className="chart-legend">
          {historicalData.length > 0 && (
            <div className="legend-item">
              <span className="legend-dot historical"></span>
              <span>Historical</span>
            </div>
          )}
          <div className="legend-item">
            <span className={`legend-dot ${mlAvailable ? 'ml-forecast' : 'statistical-forecast'}`}></span>
            <span>{mlAvailable ? 'ML Forecast' : 'Statistical Forecast'}</span>
          </div>
          {mlAvailable && (
            <div className="legend-item">
              <span className="legend-band"></span>
              <span>Confidence Band</span>
            </div>
          )}
        </div>
      </div>
      <canvas ref={canvasRef} className="forecast-canvas"></canvas>
    </div>
  );
}
