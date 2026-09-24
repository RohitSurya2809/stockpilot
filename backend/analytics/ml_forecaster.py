"""
ML-Based Demand Forecaster

Supervised machine learning approach to demand forecasting using RandomForestRegressor.

This module implements:
- Feature engineering from time series data
- Chronological train/test split (no data leakage)
- RandomForestRegressor training
- Multi-step forecasting
- Model evaluation (MAE, RMSE)

Architecture:
  Historical Sales
       ↓
  Feature Engineering
       ↓
  Random Forest Regressor
       ↓
  Demand Prediction
       ↓
  Validation Metrics
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')


def engineer_features(sales_data: List[float]) -> pd.DataFrame:
    """
    Engineer forecasting features from historical sales data.

    Features created:
    - lag_1: Previous day's demand
    - lag_7: Demand 7 days ago (weekly pattern)
    - lag_14: Demand 14 days ago
    - rolling_mean_7: 7-day rolling average
    - rolling_mean_14: 14-day rolling average
    - rolling_std_7: 7-day rolling std deviation (volatility)
    - day_of_week: Day of week (0-6)
    - day_index: Temporal index (0, 1, 2, ...)

    IMPORTANT: No data leakage - features for day N only use data from days < N

    Args:
        sales_data: Historical daily demand (chronological order)

    Returns:
        DataFrame with features and target
    """
    df = pd.DataFrame({
        'demand': sales_data,
        'day_index': range(len(sales_data))
    })

    # Lag features (previous days)
    df['lag_1'] = df['demand'].shift(1)
    df['lag_7'] = df['demand'].shift(7)
    df['lag_14'] = df['demand'].shift(14)

    # Rolling statistics (use past data only)
    df['rolling_mean_7'] = df['demand'].shift(1).rolling(window=7, min_periods=3).mean()
    df['rolling_mean_14'] = df['demand'].shift(1).rolling(window=14, min_periods=7).mean()
    df['rolling_std_7'] = df['demand'].shift(1).rolling(window=7, min_periods=3).std()

    # Temporal features
    df['day_of_week'] = df['day_index'] % 7

    # Target: next day's demand
    df['target'] = df['demand'].shift(-1)

    # Drop rows with NaN (first 14 days don't have all features, last row has no target)
    df = df.dropna()

    return df


def train_ml_forecast_model(
    sales_data: List[float],
    train_ratio: float = 0.8,
    n_estimators: int = 100,
    random_state: int = 42
) -> Dict:
    """
    Train RandomForestRegressor for demand forecasting.

    CRITICAL: Uses chronological split (NOT random shuffle) to avoid data leakage.

    Args:
        sales_data: Historical daily demand (chronological)
        train_ratio: Fraction of data for training (rest for validation)
        n_estimators: Number of trees in Random Forest
        random_state: Random seed for reproducibility

    Returns:
        Dictionary with model, validation metrics, and metadata
    """
    if len(sales_data) < 30:
        return {
            'error': 'Insufficient data for ML training (need >= 30 days)',
            'min_required': 30,
            'actual': len(sales_data)
        }

    # Engineer features
    df = engineer_features(sales_data)

    if len(df) < 20:
        return {
            'error': 'Insufficient data after feature engineering (need >= 20 samples)',
            'min_required': 20,
            'actual': len(df)
        }

    # CHRONOLOGICAL split (no shuffle!)
    split_idx = int(len(df) * train_ratio)

    if split_idx < 10 or (len(df) - split_idx) < 5:
        return {
            'error': 'Train/val split too small',
            'train_size': split_idx,
            'val_size': len(df) - split_idx
        }

    train_df = df.iloc[:split_idx]
    val_df = df.iloc[split_idx:]

    # Separate features and target
    feature_cols = ['lag_1', 'lag_7', 'lag_14', 'rolling_mean_7', 'rolling_mean_14', 'rolling_std_7', 'day_of_week', 'day_index']

    X_train = train_df[feature_cols]
    y_train = train_df['target']
    X_val = val_df[feature_cols]
    y_val = val_df['target']

    # Train Random Forest
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        random_state=random_state,
        n_jobs=-1,  # Use all CPU cores
        max_depth=10,  # Prevent overfitting
        min_samples_split=5,
        min_samples_leaf=2
    )

    model.fit(X_train, y_train)

    # Validate
    y_pred_train = model.predict(X_train)
    y_pred_val = model.predict(X_val)

    # Calculate metrics
    train_mae = mean_absolute_error(y_train, y_pred_train)
    train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))

    val_mae = mean_absolute_error(y_val, y_pred_val)
    val_rmse = np.sqrt(mean_squared_error(y_val, y_pred_val))

    return {
        'model': model,
        'feature_cols': feature_cols,
        'train_size': len(train_df),
        'val_size': len(val_df),
        'train_mae': float(train_mae),
        'train_rmse': float(train_rmse),
        'val_mae': float(val_mae),
        'val_rmse': float(val_rmse),
        'n_estimators': n_estimators,
        'last_known_demand': float(sales_data[-1]),
        'last_features': df[feature_cols].iloc[-1].to_dict()
    }


def forecast_with_ml_model(
    model_result: Dict,
    forecast_horizon_days: int,
    sales_data: List[float]
) -> Dict:
    """
    Generate multi-step forecast using trained ML model.

    Uses recursive forecasting:
    - Predict day N+1
    - Use prediction as lag feature for day N+2
    - Repeat for full horizon

    Args:
        model_result: Output from train_ml_forecast_model
        forecast_horizon_days: Number of days to forecast
        sales_data: Original sales data (needed for feature generation)

    Returns:
        Dictionary with forecast and metadata
    """
    if 'error' in model_result:
        return {
            'forecasts': [0.0] * forecast_horizon_days,
            'method': 'ml_error',
            'error': model_result['error']
        }

    model = model_result['model']
    feature_cols = model_result['feature_cols']

    # Start with last known features
    current_features = model_result['last_features'].copy()
    last_day_index = current_features['day_of_week']

    forecasts = []
    recent_values = list(sales_data[-14:])  # Keep last 14 days for rolling calculations

    for day_ahead in range(forecast_horizon_days):
        # Update temporal features
        current_features['day_index'] += 1
        current_features['day_of_week'] = (current_features['day_of_week'] + 1) % 7

        # Prepare feature vector
        X = pd.DataFrame([current_features])[feature_cols]

        # Predict
        pred = model.predict(X)[0]
        pred = max(0.0, pred)  # Demand can't be negative
        forecasts.append(float(pred))

        # Update features for next iteration (rolling window)
        recent_values.append(pred)

        # Update lag features
        current_features['lag_1'] = pred
        if len(recent_values) >= 7:
            current_features['lag_7'] = recent_values[-7]
        if len(recent_values) >= 14:
            current_features['lag_14'] = recent_values[-14]

        # Update rolling statistics
        if len(recent_values) >= 7:
            current_features['rolling_mean_7'] = float(np.mean(recent_values[-7:]))
            current_features['rolling_std_7'] = float(np.std(recent_values[-7:]))
        if len(recent_values) >= 14:
            current_features['rolling_mean_14'] = float(np.mean(recent_values[-14:]))

    return {
        'forecasts': forecasts,
        'method': 'random_forest_regressor',
        'model_name': 'RandomForestRegressor',
        'n_estimators': model_result['n_estimators'],
        'train_size': model_result['train_size'],
        'val_size': model_result['val_size'],
        'val_mae': model_result['val_mae'],
        'val_rmse': model_result['val_rmse'],
        'train_mae': model_result['train_mae'],
        'train_rmse': model_result['train_rmse'],
        'confidence_level': calculate_confidence(model_result),
        'forecast_horizon_days': forecast_horizon_days
    }


def calculate_confidence(model_result: Dict) -> float:
    """
    Calculate confidence score based on validation performance.

    Lower error relative to mean demand = higher confidence.

    Returns confidence between 0 and 1.
    """
    val_mae = model_result['val_mae']
    last_demand = model_result['last_known_demand']

    if last_demand == 0:
        return 0.5

    # MAE as percentage of demand
    error_pct = val_mae / max(last_demand, 1)

    # Convert to confidence (lower error = higher confidence)
    # 0% error = 1.0 confidence
    # 50% error = 0.5 confidence
    # 100% error = 0.0 confidence
    confidence = max(0.0, min(1.0, 1.0 - error_pct))

    return float(confidence)


def ml_forecast_demand(
    sales_data: List[float],
    forecast_horizon_days: int = 30,
    train_ratio: float = 0.8
) -> Dict:
    """
    Main entry point for ML-based forecasting.

    Complete pipeline:
    1. Feature engineering
    2. Train Random Forest
    3. Validate model
    4. Generate multi-step forecast

    Args:
        sales_data: Historical daily demand (chronological)
        forecast_horizon_days: Days to forecast
        train_ratio: Train/validation split ratio

    Returns:
        Dictionary with forecasts, metrics, and metadata
    """
    # Train model
    model_result = train_ml_forecast_model(sales_data, train_ratio=train_ratio)

    if 'error' in model_result:
        return {
            'forecasts': [0.0] * forecast_horizon_days,
            'method': 'ml_insufficient_data',
            'error': model_result['error'],
            'forecast_horizon_days': forecast_horizon_days
        }

    # Generate forecast
    forecast_result = forecast_with_ml_model(model_result, forecast_horizon_days, sales_data)

    return forecast_result


# Test module
if __name__ == "__main__":
    print("=" * 70)
    print("ML DEMAND FORECASTER - TEST")
    print("=" * 70)
    print()

    # Generate test data with increasing trend
    np.random.seed(42)
    days = 60
    base_demand = 30
    trend = 0.5
    noise = 3

    test_data = [base_demand + i * trend + np.random.normal(0, noise) for i in range(days)]

    print(f"Test data: {days} days")
    print(f"Mean demand: {np.mean(test_data):.1f}")
    print(f"Trend: +{trend} units/day")
    print()

    # Test ML forecasting
    print("Training ML model...")
    result = ml_forecast_demand(test_data, forecast_horizon_days=14)

    if 'error' in result:
        print(f"ERROR: {result['error']}")
    else:
        print(f"[OK] Model trained successfully")
        print(f"  Method: {result['method']}")
        print(f"  Model: {result['model_name']}")
        print(f"  Trees: {result['n_estimators']}")
        print(f"  Training samples: {result['train_size']}")
        print(f"  Validation samples: {result['val_size']}")
        print()
        print(f"Validation Metrics:")
        print(f"  MAE: {result['val_mae']:.2f} units/day")
        print(f"  RMSE: {result['val_rmse']:.2f} units/day")
        print(f"  Confidence: {result['confidence_level']:.1%}")
        print()
        print(f"Forecast (14 days):")
        for i, forecast in enumerate(result['forecasts'][:7], 1):
            print(f"  Day {i}: {forecast:.1f} units")
        print(f"  ...")
        print()

        avg_forecast = np.mean(result['forecasts'])
        print(f"Average forecast: {avg_forecast:.1f} units/day")
        print(f"Historical average: {np.mean(test_data[-14:]):.1f} units/day")

    print()
    print("=" * 70)
    print("ML FORECASTER TEST COMPLETE")
    print("=" * 70)
