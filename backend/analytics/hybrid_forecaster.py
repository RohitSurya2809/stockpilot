"""
Hybrid Forecaster - Integrates Statistical and ML Forecasting

This module combines:
1. Statistical forecasting (moving average + trend)
2. ML forecasting (RandomForestRegressor)

Architecture:
  Sales Data
      |
      ├─→ Statistical Forecast (baseline)
      └─→ ML Forecast (machine learning)
          |
          └─→ Combined Result with both forecasts
"""

from typing import List, Dict
from analytics.forecaster import forecast_demand as statistical_forecast
from analytics.ml_forecaster import ml_forecast_demand
import numpy as np


def hybrid_forecast_demand(
    sales_data: List[float],
    forecast_horizon_days: int = 30,
    use_ml: bool = True,
    moving_avg_window: int = 14
) -> Dict:
    """
    Generate forecast using both statistical and ML methods.

    Returns both forecasts for comparison and allows selection.

    Args:
        sales_data: Historical daily demand (chronological)
        forecast_horizon_days: Days to forecast ahead
        use_ml: Whether to attempt ML forecast
        moving_avg_window: Window for moving average

    Returns:
        Dictionary containing:
        - statistical_forecast: Baseline statistical method
        - ml_forecast: RandomForest ML method (if available)
        - selected_forecast: The forecast to use
        - comparison: Performance comparison if both available
    """
    result = {
        'forecast_horizon_days': forecast_horizon_days,
        'data_points': len(sales_data)
    }

    # Always run statistical forecast (baseline)
    stat_result = statistical_forecast(
        sales_data=sales_data,
        forecast_horizon_days=forecast_horizon_days,
        moving_avg_window=moving_avg_window,
        include_trend=True,
        include_seasonality=True
    )

    result['statistical_forecast'] = {
        'forecasts': stat_result['forecasts'],
        'method': stat_result['method'],
        'confidence_level': stat_result['confidence_level'],
        'available': 'error' not in stat_result
    }

    # Try ML forecast if enabled and sufficient data
    ml_result = None
    if use_ml and len(sales_data) >= 30:
        try:
            ml_result = ml_forecast_demand(
                sales_data=sales_data,
                forecast_horizon_days=forecast_horizon_days
            )

            if 'error' not in ml_result:
                result['ml_forecast'] = {
                    'forecasts': ml_result['forecasts'],
                    'method': ml_result['method'],
                    'model_name': ml_result['model_name'],
                    'confidence_level': ml_result['confidence_level'],
                    'val_mae': ml_result['val_mae'],
                    'val_rmse': ml_result['val_rmse'],
                    'train_size': ml_result['train_size'],
                    'val_size': ml_result['val_size'],
                    'available': True
                }
            else:
                result['ml_forecast'] = {
                    'available': False,
                    'reason': ml_result.get('error', 'ML training failed')
                }
        except Exception as e:
            result['ml_forecast'] = {
                'available': False,
                'reason': f'ML error: {str(e)}'
            }
    else:
        result['ml_forecast'] = {
            'available': False,
            'reason': f'Insufficient data for ML (need >= 30 days, have {len(sales_data)})'
        }

    # Select forecast to use
    if result['ml_forecast']['available']:
        # Use ML forecast if available and confidence is reasonable
        selected_forecasts = result['ml_forecast']['forecasts']
        selected_method = 'ml_primary'
        selected_confidence = result['ml_forecast']['confidence_level']

        result['selected_forecast'] = {
            'forecasts': selected_forecasts,
            'method': selected_method,
            'confidence_level': selected_confidence,
            'source': 'ml'
        }

        # Calculate comparison metrics
        ml_avg = np.mean(result['ml_forecast']['forecasts'])
        stat_avg = np.mean(result['statistical_forecast']['forecasts'])
        diff = ml_avg - stat_avg
        diff_pct = (diff / stat_avg * 100) if stat_avg > 0 else 0

        result['comparison'] = {
            'ml_average': float(ml_avg),
            'statistical_average': float(stat_avg),
            'difference': float(diff),
            'difference_percent': float(diff_pct)
        }
    else:
        # Fall back to statistical forecast
        selected_forecasts = result['statistical_forecast']['forecasts']
        selected_method = 'statistical_fallback'
        selected_confidence = result['statistical_forecast']['confidence_level']

        result['selected_forecast'] = {
            'forecasts': selected_forecasts,
            'method': selected_method,
            'confidence_level': selected_confidence,
            'source': 'statistical',
            'fallback_reason': result['ml_forecast']['reason']
        }

    return result


def get_hybrid_forecast_for_lead_time(
    sales_data: List[float],
    lead_time_days: int,
    use_ml: bool = True
) -> Dict:
    """
    Get hybrid forecast specifically for supplier lead time.

    Used by dynamic reorder point calculation.

    Args:
        sales_data: Historical daily demand
        lead_time_days: Supplier lead time
        use_ml: Whether to use ML forecast

    Returns:
        Forecast with avg_daily_demand for lead time period
    """
    result = hybrid_forecast_demand(
        sales_data=sales_data,
        forecast_horizon_days=lead_time_days,
        use_ml=use_ml
    )

    # Calculate average daily demand from selected forecast
    selected = result['selected_forecast']
    lead_time_forecasts = selected['forecasts']

    total_demand = sum(lead_time_forecasts)
    avg_daily_demand = total_demand / lead_time_days if lead_time_days > 0 else 0.0

    return {
        'avg_daily_demand': float(avg_daily_demand),
        'total_demand_during_lead_time': float(total_demand),
        'forecast_method': selected['method'],
        'confidence_level': selected['confidence_level'],
        'source': selected['source'],
        'forecasts': lead_time_forecasts,
        'ml_available': result['ml_forecast']['available']
    }


# Test module
if __name__ == "__main__":
    print("=" * 70)
    print("HYBRID FORECASTER - TEST")
    print("=" * 70)
    print()

    # Test data: increasing trend
    import numpy as np
    np.random.seed(42)
    test_data = [30 + i * 0.5 + np.random.normal(0, 3) for i in range(60)]

    print(f"Test data: {len(test_data)} days")
    print(f"Average demand: {np.mean(test_data):.1f} units/day")
    print()

    # Test hybrid forecast
    print("Running hybrid forecast...")
    result = hybrid_forecast_demand(test_data, forecast_horizon_days=14)

    print()
    print("STATISTICAL FORECAST:")
    print("-" * 70)
    if result['statistical_forecast']['available']:
        stat = result['statistical_forecast']
        print(f"  Method: {stat['method']}")
        print(f"  Confidence: {stat['confidence_level']:.1%}")
        print(f"  Average: {np.mean(stat['forecasts']):.1f} units/day")
    else:
        print("  Not available")

    print()
    print("ML FORECAST:")
    print("-" * 70)
    if result['ml_forecast']['available']:
        ml = result['ml_forecast']
        print(f"  Model: {ml['model_name']}")
        print(f"  Method: {ml['method']}")
        print(f"  Validation MAE: {ml['val_mae']:.2f} units")
        print(f"  Validation RMSE: {ml['val_rmse']:.2f} units")
        print(f"  Confidence: {ml['confidence_level']:.1%}")
        print(f"  Average: {np.mean(ml['forecasts']):.1f} units/day")
    else:
        print(f"  Not available: {result['ml_forecast']['reason']}")

    print()
    print("SELECTED FORECAST:")
    print("-" * 70)
    selected = result['selected_forecast']
    print(f"  Source: {selected['source'].upper()}")
    print(f"  Method: {selected['method']}")
    print(f"  Confidence: {selected['confidence_level']:.1%}")
    print(f"  Average: {np.mean(selected['forecasts']):.1f} units/day")

    if 'comparison' in result:
        print()
        print("COMPARISON:")
        print("-" * 70)
        comp = result['comparison']
        print(f"  ML forecast: {comp['ml_average']:.1f} units/day")
        print(f"  Statistical: {comp['statistical_average']:.1f} units/day")
        print(f"  Difference: {comp['difference']:+.1f} units/day ({comp['difference_percent']:+.1f}%)")

    print()
    print("=" * 70)
    print("HYBRID FORECASTER TEST COMPLETE")
    print("=" * 70)
