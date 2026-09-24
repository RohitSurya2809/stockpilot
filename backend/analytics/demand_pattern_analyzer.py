"""
Demand Pattern Analyzer

Analyzes historical sales data to detect:
- Trend (increasing, decreasing, stable)
- Seasonality (weekly, monthly patterns)
- Volatility (demand variability)
- Recent average demand

All algorithms are deterministic and explainable (not LLM-based).
"""

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LinearRegression
from typing import Dict, List, Tuple, Optional
from datetime import date


def analyze_trend(
    sales_data: List[float],
    window_days: int = 30,
    threshold_percentage: float = 5.0
) -> Dict:
    """
    Detect demand trend using linear regression.

    Args:
        sales_data: List of daily demand values (chronological order)
        window_days: Number of recent days to analyze (default: 30)
        threshold_percentage: % change threshold to classify as increasing/decreasing

    Returns:
        Dictionary with trend analysis:
        {
            'trend': 'increasing' | 'decreasing' | 'stable',
            'trend_percentage': float,  # % change over period
            'trend_strength': float,    # R² value (0-1)
            'slope': float,             # Daily change rate
            'recent_window_days': int
        }
    """
    if len(sales_data) < 7:
        return {
            'trend': 'unknown',
            'trend_percentage': 0.0,
            'trend_strength': 0.0,
            'slope': 0.0,
            'recent_window_days': len(sales_data),
            'error': 'Insufficient data for trend analysis (need at least 7 days)'
        }

    # Use most recent data within window
    recent_sales = sales_data[-min(window_days, len(sales_data)):]
    actual_window = len(recent_sales)

    # Prepare data for linear regression
    X = np.array(range(actual_window)).reshape(-1, 1)  # Days
    y = np.array(recent_sales)  # Demand

    # Fit linear model
    model = LinearRegression()
    model.fit(X, y)

    slope = model.coef_[0]
    r_squared = model.score(X, y)

    # Calculate trend percentage
    avg_demand = np.mean(recent_sales)
    if avg_demand > 0:
        # Total change over period divided by average
        total_change = slope * actual_window
        trend_percentage = (total_change / avg_demand) * 100
    else:
        trend_percentage = 0.0

    # Classify trend
    if trend_percentage > threshold_percentage:
        trend = 'increasing'
    elif trend_percentage < -threshold_percentage:
        trend = 'decreasing'
    else:
        trend = 'stable'

    return {
        'trend': trend,
        'trend_percentage': round(trend_percentage, 2),
        'trend_strength': round(r_squared, 3),
        'slope': round(slope, 3),
        'recent_window_days': actual_window,
        'average_demand': round(avg_demand, 2)
    }


def detect_seasonality(
    sales_data: List[float],
    period: int = 7,
    correlation_threshold: float = 0.5
) -> Dict:
    """
    Detect seasonal patterns using autocorrelation.

    Args:
        sales_data: List of daily demand values
        period: Seasonality period to check (7 = weekly, 30 = monthly)
        correlation_threshold: Minimum correlation to consider seasonal

    Returns:
        Dictionary with seasonality analysis:
        {
            'has_seasonality': bool,
            'period': int,
            'autocorrelation': float,
            'seasonal_factors': List[float],  # Multipliers for each day in period
            'confidence': str
        }
    """
    if len(sales_data) < period * 3:
        return {
            'has_seasonality': False,
            'period': period,
            'autocorrelation': 0.0,
            'seasonal_factors': None,
            'confidence': 'insufficient_data',
            'error': f'Need at least {period * 3} days for seasonality detection'
        }

    # Calculate autocorrelation at the specified lag
    series = pd.Series(sales_data)
    autocorr = series.autocorr(lag=period)

    # Handle NaN (can occur with very flat data)
    if pd.isna(autocorr):
        autocorr = 0.0

    has_seasonality = bool(abs(autocorr) > correlation_threshold)

    if has_seasonality:
        # Calculate seasonal factors (multipliers for each day in period)
        seasonal_avg = []
        overall_avg = np.mean(sales_data)

        for day_in_period in range(period):
            # Get all values for this day of the period
            period_values = [
                sales_data[i]
                for i in range(day_in_period, len(sales_data), period)
            ]
            if period_values:
                day_avg = np.mean(period_values)
                # Factor relative to overall average
                factor = day_avg / overall_avg if overall_avg > 0 else 1.0
                seasonal_avg.append(round(factor, 3))
            else:
                seasonal_avg.append(1.0)

        # Confidence based on correlation strength
        if abs(autocorr) > 0.7:
            confidence = 'high'
        elif abs(autocorr) > 0.5:
            confidence = 'medium'
        else:
            confidence = 'low'

        return {
            'has_seasonality': True,
            'period': period,
            'autocorrelation': round(autocorr, 3),
            'seasonal_factors': seasonal_avg,
            'confidence': confidence
        }
    else:
        return {
            'has_seasonality': False,
            'period': period,
            'autocorrelation': round(autocorr, 3),
            'seasonal_factors': None,
            'confidence': 'none'
        }


def calculate_volatility(sales_data: List[float]) -> Dict:
    """
    Calculate demand volatility using coefficient of variation.

    Args:
        sales_data: List of daily demand values

    Returns:
        Dictionary with volatility metrics:
        {
            'coefficient_of_variation': float,  # CV = std / mean
            'volatility_level': str,           # 'low', 'medium', 'high'
            'std_deviation': float,
            'mean_demand': float
        }
    """
    if len(sales_data) < 2:
        return {
            'coefficient_of_variation': 0.0,
            'volatility_level': 'unknown',
            'std_deviation': 0.0,
            'mean_demand': 0.0,
            'error': 'Insufficient data for volatility calculation'
        }

    mean_demand = np.mean(sales_data)
    std_dev = np.std(sales_data)

    # Coefficient of Variation
    if mean_demand > 0:
        cv = std_dev / mean_demand
    else:
        cv = 0.0

    # Classify volatility
    if cv > 0.3:
        volatility_level = 'high'
    elif cv > 0.15:
        volatility_level = 'medium'
    else:
        volatility_level = 'low'

    return {
        'coefficient_of_variation': round(cv, 3),
        'volatility_level': volatility_level,
        'std_deviation': round(std_dev, 2),
        'mean_demand': round(mean_demand, 2)
    }


def calculate_recent_average(
    sales_data: List[float],
    window_days: int = 14
) -> Dict:
    """
    Calculate recent average demand (moving average).

    Args:
        sales_data: List of daily demand values
        window_days: Number of recent days to average

    Returns:
        Dictionary with recent average metrics
    """
    if not sales_data:
        return {
            'recent_average': 0.0,
            'window_days': 0,
            'error': 'No sales data'
        }

    actual_window = min(window_days, len(sales_data))
    recent_sales = sales_data[-actual_window:]
    recent_avg = np.mean(recent_sales)

    return {
        'recent_average': round(recent_avg, 2),
        'window_days': actual_window,
        'data_points': len(recent_sales)
    }


def analyze_demand_pattern(
    sales_data: List[float],
    analysis_window_days: int = 30,
    moving_avg_window: int = 14
) -> Dict:
    """
    Comprehensive demand pattern analysis.

    Combines trend, seasonality, volatility, and recent average analysis.

    Args:
        sales_data: List of daily demand values (chronological order)
        analysis_window_days: Days to analyze for trend
        moving_avg_window: Days for moving average

    Returns:
        Complete demand pattern analysis dictionary
    """
    if not sales_data or len(sales_data) < 7:
        return {
            'error': 'Insufficient data for analysis (need at least 7 days)',
            'data_points': len(sales_data) if sales_data else 0
        }

    # Run all analyses
    trend_analysis = analyze_trend(sales_data, window_days=analysis_window_days)
    seasonality_analysis = detect_seasonality(sales_data, period=7)  # Weekly
    volatility_analysis = calculate_volatility(sales_data)
    recent_avg_analysis = calculate_recent_average(sales_data, window_days=moving_avg_window)

    # Combine results
    analysis = {
        'trend': trend_analysis,
        'seasonality': seasonality_analysis,
        'volatility': volatility_analysis,
        'recent_average': recent_avg_analysis,
        'data_summary': {
            'total_data_points': len(sales_data),
            'total_demand': round(sum(sales_data), 2),
            'overall_average': round(np.mean(sales_data), 2),
            'min_demand': round(min(sales_data), 2),
            'max_demand': round(max(sales_data), 2)
        }
    }

    return analysis


def generate_pattern_summary(analysis: Dict) -> str:
    """
    Generate human-readable summary of demand pattern analysis.

    Args:
        analysis: Output from analyze_demand_pattern()

    Returns:
        Human-readable summary string
    """
    if 'error' in analysis:
        return f"Analysis Error: {analysis['error']}"

    trend = analysis['trend']
    volatility = analysis['volatility']
    recent_avg = analysis['recent_average']

    summary_parts = []

    # Trend summary
    if trend['trend'] == 'increasing':
        summary_parts.append(
            f"Demand is increasing by {abs(trend['trend_percentage']):.1f}% "
            f"over the last {trend['recent_window_days']} days"
        )
    elif trend['trend'] == 'decreasing':
        summary_parts.append(
            f"Demand is decreasing by {abs(trend['trend_percentage']):.1f}% "
            f"over the last {trend['recent_window_days']} days"
        )
    else:
        summary_parts.append(
            f"Demand is stable (within ±5%) over the last {trend['recent_window_days']} days"
        )

    # Recent average
    summary_parts.append(
        f"Recent average demand: {recent_avg['recent_average']:.1f} units/day "
        f"(last {recent_avg['window_days']} days)"
    )

    # Volatility
    summary_parts.append(
        f"Demand volatility: {volatility['volatility_level']} "
        f"(CV: {volatility['coefficient_of_variation']:.2f})"
    )

    # Seasonality
    seasonality = analysis['seasonality']
    if seasonality['has_seasonality']:
        summary_parts.append(
            f"Weekly seasonality detected (correlation: {seasonality['autocorrelation']:.2f}, "
            f"confidence: {seasonality['confidence']})"
        )
    else:
        summary_parts.append("No significant seasonality detected")

    return ". ".join(summary_parts) + "."


# Example usage and testing
if __name__ == "__main__":
    # Test with sample data
    print("="*70)
    print("DEMAND PATTERN ANALYZER - TEST")
    print("="*70)

    # Generate sample data with increasing trend
    np.random.seed(42)
    days = 60
    base_demand = 20
    trend_data = [base_demand + i * 0.5 + np.random.normal(0, 2) for i in range(days)]

    print("\nTest 1: Increasing Trend")
    print("-" * 70)
    analysis = analyze_demand_pattern(trend_data)
    print(generate_pattern_summary(analysis))
    print(f"\nTrend: {analysis['trend']['trend']} ({analysis['trend']['trend_percentage']}%)")
    print(f"Volatility: {analysis['volatility']['volatility_level']}")

    print("\n" + "="*70)
