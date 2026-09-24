"""
Demand Forecaster

Generates future demand predictions using:
- Moving average as baseline
- Trend adjustment
- Seasonality factors

Simple, robust, and explainable approach (not overly complex ML).
All calculations are deterministic.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional
from analytics.demand_pattern_analyzer import analyze_demand_pattern


def forecast_demand(
    sales_data: List[float],
    forecast_horizon_days: int,
    moving_avg_window: int = 14,
    include_trend: bool = True,
    include_seasonality: bool = True
) -> Dict:
    """
    Forecast future demand using moving average + trend + seasonality.

    Method:
    1. Calculate moving average from recent data
    2. Apply trend adjustment if trend detected
    3. Apply seasonality factors if pattern detected
    4. Generate daily forecasts for horizon

    Args:
        sales_data: Historical daily demand (chronological order)
        forecast_horizon_days: Number of days to forecast
        moving_avg_window: Days for moving average calculation
        include_trend: Whether to adjust for trend
        include_seasonality: Whether to apply seasonal factors

    Returns:
        Dictionary with forecast data and metadata:
        {
            'forecasts': List[float],  # Daily forecasted demand
            'method': str,              # Method description
            'confidence_level': float,  # Estimated confidence (0-1)
            'pattern_analysis': Dict,   # Pattern analysis used
            'forecast_horizon_days': int
        }
    """
    if not sales_data or len(sales_data) < 7:
        return {
            'forecasts': [0.0] * forecast_horizon_days,
            'method': 'insufficient_data',
            'confidence_level': 0.0,
            'error': 'Insufficient historical data for forecasting',
            'forecast_horizon_days': forecast_horizon_days
        }

    # Analyze demand pattern
    pattern = analyze_demand_pattern(
        sales_data,
        moving_avg_window=moving_avg_window
    )

    if 'error' in pattern:
        return {
            'forecasts': [0.0] * forecast_horizon_days,
            'method': 'analysis_error',
            'confidence_level': 0.0,
            'error': pattern['error'],
            'forecast_horizon_days': forecast_horizon_days
        }

    # Extract pattern components
    trend_info = pattern['trend']
    seasonality_info = pattern['seasonality']
    recent_avg = pattern['recent_average']['recent_average']

    # Start with moving average as baseline
    base_forecast = recent_avg

    # Prepare method description
    method_parts = ['moving_average']
    if include_trend and trend_info['trend'] != 'stable':
        method_parts.append('trend_adjustment')
    if include_seasonality and seasonality_info['has_seasonality']:
        method_parts.append('seasonality')

    method = '+'.join(method_parts)

    # Generate forecasts for each day
    forecasts = []
    trend_slope = trend_info['slope'] if include_trend else 0.0
    last_day_index = len(sales_data) - 1

    for day_ahead in range(1, forecast_horizon_days + 1):
        forecast_day_index = last_day_index + day_ahead

        # Start with baseline (moving average)
        forecast = base_forecast

        # Add trend component
        if include_trend and trend_info['trend'] != 'stable':
            # Project trend forward
            # Use the slope from trend analysis
            trend_adjustment = trend_slope * day_ahead
            forecast += trend_adjustment

        # Apply seasonality
        if include_seasonality and seasonality_info['has_seasonality']:
            period = seasonality_info['period']
            seasonal_factors = seasonality_info['seasonal_factors']

            # Determine which day in the seasonal cycle
            seasonal_day = forecast_day_index % period
            seasonal_factor = seasonal_factors[seasonal_day]

            # Apply seasonal multiplier
            forecast *= seasonal_factor

        # Ensure non-negative forecast
        forecast = max(0.0, forecast)

        forecasts.append(round(forecast, 2))

    # Estimate confidence level
    # Lower confidence for:
    # - High volatility
    # - Weak trend strength
    # - Longer forecast horizon
    confidence = 0.8  # Base confidence

    volatility_cv = pattern['volatility']['coefficient_of_variation']
    if volatility_cv > 0.3:
        confidence *= 0.7  # High volatility reduces confidence
    elif volatility_cv > 0.15:
        confidence *= 0.85

    # Trend strength affects confidence
    if include_trend:
        trend_strength = trend_info['trend_strength']
        confidence *= (0.7 + 0.3 * trend_strength)  # Scale by R²

    # Longer horizons are less confident
    if forecast_horizon_days > 30:
        confidence *= 0.8
    elif forecast_horizon_days > 14:
        confidence *= 0.9

    confidence = round(min(confidence, 0.95), 3)  # Cap at 95%

    return {
        'forecasts': forecasts,
        'method': method,
        'confidence_level': confidence,
        'pattern_analysis': pattern,
        'forecast_horizon_days': forecast_horizon_days,
        'baseline_moving_average': round(base_forecast, 2),
        'trend_adjustment_enabled': include_trend,
        'seasonality_adjustment_enabled': include_seasonality
    }


def get_forecast_for_lead_time(
    sales_data: List[float],
    lead_time_days: int,
    moving_avg_window: int = 14
) -> Dict:
    """
    Get forecast specifically for supplier lead time period.

    This is used for dynamic reorder point calculation.

    Args:
        sales_data: Historical daily demand
        lead_time_days: Supplier lead time in days
        moving_avg_window: Days for moving average

    Returns:
        Forecast dictionary with demand during lead time
    """
    forecast_result = forecast_demand(
        sales_data=sales_data,
        forecast_horizon_days=lead_time_days,
        moving_avg_window=moving_avg_window,
        include_trend=True,
        include_seasonality=True
    )

    if 'error' in forecast_result:
        return forecast_result

    # Calculate total and average demand during lead time
    lead_time_forecasts = forecast_result['forecasts']
    total_demand_during_lead_time = sum(lead_time_forecasts)
    avg_daily_demand = total_demand_during_lead_time / lead_time_days if lead_time_days > 0 else 0.0

    return {
        'lead_time_days': lead_time_days,
        'forecasted_daily_demand': lead_time_forecasts,
        'total_demand_during_lead_time': round(total_demand_during_lead_time, 2),
        'avg_daily_demand_during_lead_time': round(avg_daily_demand, 2),
        'confidence_level': forecast_result['confidence_level'],
        'method': forecast_result['method']
    }


def generate_forecast_summary(forecast_result: Dict) -> str:
    """
    Generate human-readable forecast summary.

    Args:
        forecast_result: Output from forecast_demand()

    Returns:
        Human-readable summary string
    """
    if 'error' in forecast_result:
        return f"Forecast Error: {forecast_result['error']}"

    method = forecast_result['method'].replace('_', ' ').replace('+', ' + ')
    horizon = forecast_result['forecast_horizon_days']
    confidence = forecast_result['confidence_level'] * 100
    forecasts = forecast_result['forecasts']

    avg_forecast = np.mean(forecasts)
    baseline = forecast_result.get('baseline_moving_average', avg_forecast)

    summary = (
        f"Forecast method: {method}. "
        f"Average forecasted demand: {avg_forecast:.1f} units/day over next {horizon} days. "
        f"Baseline (recent average): {baseline:.1f} units/day. "
        f"Confidence: {confidence:.0f}%."
    )

    # Add trend info if applicable
    pattern = forecast_result.get('pattern_analysis', {})
    if pattern and 'trend' in pattern:
        trend_info = pattern['trend']
        if trend_info['trend'] != 'stable':
            summary += f" Trend: {trend_info['trend']} ({trend_info['trend_percentage']:.1f}%)."

    return summary


def validate_forecast_accuracy(
    actual_demand: List[float],
    forecasted_demand: List[float]
) -> Dict:
    """
    Validate forecast accuracy by comparing with actual demand.

    Useful for testing and model validation.

    Args:
        actual_demand: Actual observed demand
        forecasted_demand: Forecasted demand for same period

    Returns:
        Accuracy metrics:
        {
            'mean_absolute_error': float,
            'mean_absolute_percentage_error': float,
            'rmse': float,  # Root Mean Square Error
            'accuracy_score': float  # 0-1, higher is better
        }
    """
    if len(actual_demand) != len(forecasted_demand):
        return {
            'error': 'Mismatched lengths between actual and forecasted data'
        }

    actual = np.array(actual_demand)
    forecast = np.array(forecasted_demand)

    # Mean Absolute Error
    mae = np.mean(np.abs(actual - forecast))

    # Mean Absolute Percentage Error
    # Avoid division by zero
    non_zero_mask = actual != 0
    if np.any(non_zero_mask):
        mape = np.mean(np.abs((actual[non_zero_mask] - forecast[non_zero_mask]) / actual[non_zero_mask])) * 100
    else:
        mape = 0.0

    # Root Mean Square Error
    rmse = np.sqrt(np.mean((actual - forecast) ** 2))

    # Accuracy score (inverse of MAPE, capped at 1)
    accuracy = max(0.0, 1.0 - (mape / 100))

    return {
        'mean_absolute_error': round(mae, 2),
        'mean_absolute_percentage_error': round(mape, 2),
        'rmse': round(rmse, 2),
        'accuracy_score': round(accuracy, 3),
        'data_points_compared': len(actual_demand)
    }


# Example usage and testing
if __name__ == "__main__":
    print("="*70)
    print("DEMAND FORECASTER - TEST")
    print("="*70)

    # Generate sample data with trend
    np.random.seed(42)
    days_history = 60
    base_demand = 20
    historical_data = [base_demand + i * 0.5 + np.random.normal(0, 2) for i in range(days_history)]

    print("\nTest 1: 30-Day Forecast with Trend")
    print("-" * 70)
    forecast_result = forecast_demand(
        sales_data=historical_data,
        forecast_horizon_days=30,
        moving_avg_window=14,
        include_trend=True,
        include_seasonality=True
    )

    print(generate_forecast_summary(forecast_result))
    print(f"\nFirst 7 days forecast: {forecast_result['forecasts'][:7]}")
    print(f"Confidence: {forecast_result['confidence_level']}")

    print("\nTest 2: Lead Time Forecast (7 days)")
    print("-" * 70)
    lead_time_forecast = get_forecast_for_lead_time(
        sales_data=historical_data,
        lead_time_days=7,
        moving_avg_window=14
    )

    print(f"Total demand during lead time: {lead_time_forecast['total_demand_during_lead_time']:.1f} units")
    print(f"Average daily demand: {lead_time_forecast['avg_daily_demand_during_lead_time']:.1f} units/day")
    print(f"Confidence: {lead_time_forecast['confidence_level']}")

    print("\n" + "="*70)
