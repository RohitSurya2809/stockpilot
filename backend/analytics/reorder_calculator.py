"""
Dynamic Reorder Point Calculator

Calculates intelligent reorder points that adapt to:
- Forecasted demand during supplier lead time
- Demand variability (volatility)
- Desired service level
- Supplier lead time

Formula:
ROP = (Average Demand × Lead Time) + Safety Stock
Safety Stock = Z-score(service_level) × σ_demand × √(lead_time)

All calculations are deterministic and explainable.
"""

import numpy as np
from scipy import stats
from typing import Dict, List, Optional
from analytics.forecaster import get_forecast_for_lead_time


def calculate_safety_stock(
    demand_std_deviation: float,
    lead_time_days: int,
    service_level: float = 0.95
) -> Dict:
    """
    Calculate safety stock based on demand variability and service level.

    Formula: Safety Stock = Z × σ_demand × √(lead_time)

    Where:
    - Z = Z-score for desired service level (e.g., 1.65 for 95%)
    - σ_demand = Standard deviation of demand
    - lead_time = Supplier lead time in days

    Args:
        demand_std_deviation: Standard deviation of historical demand
        lead_time_days: Supplier lead time in days
        service_level: Target service level (default: 0.95 = 95%)

    Returns:
        Dictionary with safety stock calculation:
        {
            'safety_stock': float,
            'z_score': float,
            'service_level': float,
            'demand_std_deviation': float,
            'lead_time_days': int
        }
    """
    # Calculate Z-score for service level
    # For 95% service level, Z ≈ 1.65
    # For 99% service level, Z ≈ 2.33
    z_score = stats.norm.ppf(service_level)

    # Safety stock formula
    # sqrt(lead_time) accounts for demand uncertainty accumulating over time
    safety_stock = z_score * demand_std_deviation * np.sqrt(lead_time_days)

    return {
        'safety_stock': round(max(0, safety_stock), 2),
        'z_score': round(z_score, 3),
        'service_level': service_level,
        'demand_std_deviation': round(demand_std_deviation, 2),
        'lead_time_days': lead_time_days,
        'formula': f"Z({service_level}) × σ({demand_std_deviation:.1f}) × √({lead_time_days})"
    }


def calculate_dynamic_reorder_point(
    sales_data: List[float],
    supplier_lead_time_days: int,
    service_level: float = 0.95,
    moving_avg_window: int = 14
) -> Dict:
    """
    Calculate dynamic reorder point based on forecasted demand and risk.

    This is the CORE INTELLIGENCE of StockPilot.

    Formula:
    ROP = Expected Demand During Lead Time + Safety Stock

    Where:
    - Expected Demand = Avg Daily Demand × Lead Time
    - Safety Stock = Z-score × σ_demand × √(lead_time)

    Args:
        sales_data: Historical daily demand data
        supplier_lead_time_days: Supplier lead time in days
        service_level: Target service level (0-1)
        moving_avg_window: Window for recent average

    Returns:
        Complete reorder point calculation with all components
    """
    if not sales_data or len(sales_data) < 7:
        return {
            'error': 'Insufficient historical data for reorder point calculation',
            'dynamic_reorder_point': 0,
            'service_level': service_level
        }

    # Get forecast for lead time period
    lead_time_forecast = get_forecast_for_lead_time(
        sales_data=sales_data,
        lead_time_days=supplier_lead_time_days,
        moving_avg_window=moving_avg_window
    )

    if 'error' in lead_time_forecast:
        return {
            'error': lead_time_forecast['error'],
            'dynamic_reorder_point': 0,
            'service_level': service_level
        }

    # Expected demand during lead time
    expected_demand_during_lead_time = lead_time_forecast['total_demand_during_lead_time']
    avg_daily_demand = lead_time_forecast['avg_daily_demand_during_lead_time']

    # Calculate demand standard deviation from historical data
    demand_std_dev = np.std(sales_data)

    # Calculate safety stock
    safety_stock_calc = calculate_safety_stock(
        demand_std_deviation=demand_std_dev,
        lead_time_days=supplier_lead_time_days,
        service_level=service_level
    )

    safety_stock = safety_stock_calc['safety_stock']
    z_score = safety_stock_calc['z_score']

    # Dynamic Reorder Point = Expected Demand + Safety Stock
    dynamic_rop = expected_demand_during_lead_time + safety_stock

    return {
        'dynamic_reorder_point': round(dynamic_rop, 0),
        'expected_demand_during_lead_time': round(expected_demand_during_lead_time, 2),
        'safety_stock': round(safety_stock, 2),
        'avg_daily_demand': round(avg_daily_demand, 2),
        'demand_std_deviation': round(demand_std_dev, 2),
        'supplier_lead_time_days': supplier_lead_time_days,
        'service_level': service_level,
        'z_score': round(z_score, 3),
        'confidence_level': lead_time_forecast['confidence_level'],
        'forecast_method': lead_time_forecast['method'],
        'calculation_breakdown': {
            'component_1_expected_demand': round(expected_demand_during_lead_time, 2),
            'component_2_safety_stock': round(safety_stock, 2),
            'total_reorder_point': round(dynamic_rop, 0)
        }
    }


def compare_with_fixed_threshold(
    dynamic_rop: float,
    fixed_threshold: float,
    current_stock: int,
    recent_avg_demand: float
) -> Dict:
    """
    Compare dynamic ROP with traditional fixed threshold.

    This helps demonstrate StockPilot's advantage.

    Args:
        dynamic_rop: StockPilot's calculated dynamic ROP
        fixed_threshold: Traditional fixed reorder point
        current_stock: Current inventory level
        recent_avg_demand: Recent average daily demand

    Returns:
        Comparison analysis
    """
    difference = dynamic_rop - fixed_threshold
    difference_pct = (difference / fixed_threshold * 100) if fixed_threshold > 0 else 0

    # Determine which system would trigger reorder
    dynamic_triggers = current_stock <= dynamic_rop
    fixed_triggers = current_stock <= fixed_threshold

    # Days of cover (how many days current stock lasts)
    days_of_cover = current_stock / recent_avg_demand if recent_avg_demand > 0 else 0

    return {
        'dynamic_reorder_point': round(dynamic_rop, 0),
        'fixed_threshold': round(fixed_threshold, 0),
        'difference': round(difference, 0),
        'difference_percentage': round(difference_pct, 1),
        'current_stock': current_stock,
        'dynamic_system_triggers': dynamic_triggers,
        'fixed_system_triggers': fixed_triggers,
        'days_of_inventory_cover': round(days_of_cover, 1),
        'advantage': 'dynamic' if dynamic_triggers and not fixed_triggers else 'fixed' if fixed_triggers and not dynamic_triggers else 'same'
    }


def generate_reorder_explanation(rop_calculation: Dict) -> str:
    """
    Generate human-readable explanation of reorder point calculation.

    Args:
        rop_calculation: Output from calculate_dynamic_reorder_point()

    Returns:
        Human-readable explanation
    """
    if 'error' in rop_calculation:
        return f"Calculation Error: {rop_calculation['error']}"

    rop = rop_calculation['dynamic_reorder_point']
    expected_demand = rop_calculation['expected_demand_during_lead_time']
    safety_stock = rop_calculation['safety_stock']
    lead_time = rop_calculation['supplier_lead_time_days']
    avg_demand = rop_calculation['avg_daily_demand']
    service_level = rop_calculation['service_level'] * 100
    z_score = rop_calculation['z_score']

    explanation = (
        f"Dynamic Reorder Point: {rop:.0f} units. "
        f"Calculation: Expected demand during {lead_time}-day lead time ({expected_demand:.1f} units, "
        f"based on forecasted {avg_demand:.1f} units/day) "
        f"+ Safety stock ({safety_stock:.1f} units, "
        f"for {service_level:.0f}% service level, Z-score={z_score:.2f}). "
        f"This adapts to demand patterns and ensures stock availability during supplier replenishment."
    )

    return explanation


def calculate_order_quantity(
    sales_data: List[float],
    current_inventory: int,
    dynamic_rop: float,
    supplier_lead_time_days: int,
    minimum_order_quantity: int = 1
) -> Dict:
    """
    Calculate recommended order quantity.

    Simple approach for hackathon MVP:
    Order enough to cover lead time + reach target inventory level

    Args:
        sales_data: Historical demand
        current_inventory: Current stock level
        dynamic_rop: Calculated dynamic reorder point
        supplier_lead_time_days: Lead time in days
        minimum_order_quantity: Supplier's minimum order qty

    Returns:
        Order quantity recommendation
    """
    # Get forecast for lead time
    lead_time_forecast = get_forecast_for_lead_time(
        sales_data=sales_data,
        lead_time_days=supplier_lead_time_days
    )

    if 'error' in lead_time_forecast:
        return {
            'error': lead_time_forecast['error'],
            'order_quantity': minimum_order_quantity
        }

    demand_during_lead_time = lead_time_forecast['total_demand_during_lead_time']

    # Target inventory = 2x dynamic ROP (conservative)
    target_inventory = dynamic_rop * 2

    # Order quantity = demand during lead time + target - current inventory
    order_qty = int(demand_during_lead_time + target_inventory - current_inventory)

    # Respect minimum order quantity
    order_qty = max(order_qty, minimum_order_quantity)

    # Round to nearest 50 for practical ordering (optional)
    order_qty = int(np.ceil(order_qty / 50) * 50)

    return {
        'order_quantity': order_qty,
        'demand_during_lead_time': round(demand_during_lead_time, 2),
        'target_inventory': round(target_inventory, 0),
        'current_inventory': current_inventory,
        'minimum_order_quantity': minimum_order_quantity,
        'reasoning': f"Order {order_qty} units to cover forecasted demand ({demand_during_lead_time:.0f}) during lead time and reach target inventory level ({target_inventory:.0f})"
    }


# Example usage and testing
if __name__ == "__main__":
    print("="*70)
    print("DYNAMIC REORDER POINT CALCULATOR - TEST")
    print("="*70)

    # Generate sample data with increasing trend (mimics demo scenario)
    np.random.seed(42)
    days_history = 60
    base_demand = 20
    historical_data = [base_demand + i * 0.5 + np.random.normal(0, 2) for i in range(days_history)]

    print("\nTest 1: Calculate Dynamic ROP for 7-day lead time")
    print("-" * 70)

    rop_calc = calculate_dynamic_reorder_point(
        sales_data=historical_data,
        supplier_lead_time_days=7,
        service_level=0.95,
        moving_avg_window=14
    )

    print(generate_reorder_explanation(rop_calc))
    print(f"\nBreakdown:")
    print(f"  Expected Demand: {rop_calc['expected_demand_during_lead_time']:.1f} units")
    print(f"  Safety Stock: {rop_calc['safety_stock']:.1f} units")
    print(f"  Dynamic ROP: {rop_calc['dynamic_reorder_point']:.0f} units")

    print("\nTest 2: Compare with Fixed Threshold (100 units)")
    print("-" * 70)

    current_stock = 184
    fixed_threshold = 100

    comparison = compare_with_fixed_threshold(
        dynamic_rop=rop_calc['dynamic_reorder_point'],
        fixed_threshold=fixed_threshold,
        current_stock=current_stock,
        recent_avg_demand=rop_calc['avg_daily_demand']
    )

    print(f"Current Stock: {comparison['current_stock']} units")
    print(f"Fixed Threshold: {comparison['fixed_threshold']} units")
    print(f"Dynamic ROP: {comparison['dynamic_reorder_point']} units")
    print(f"Difference: {comparison['difference']:+.0f} units ({comparison['difference_percentage']:+.1f}%)")
    print(f"Days of Cover: {comparison['days_of_inventory_cover']:.1f} days")
    print(f"Fixed system triggers: {comparison['fixed_system_triggers']}")
    print(f"Dynamic system triggers: {comparison['dynamic_system_triggers']}")

    print("\nTest 3: Calculate Order Quantity")
    print("-" * 70)

    order_calc = calculate_order_quantity(
        sales_data=historical_data,
        current_inventory=current_stock,
        dynamic_rop=rop_calc['dynamic_reorder_point'],
        supplier_lead_time_days=7,
        minimum_order_quantity=50
    )

    print(f"Recommended Order: {order_calc['order_quantity']} units")
    print(f"Reasoning: {order_calc['reasoning']}")

    print("\n" + "="*70)
