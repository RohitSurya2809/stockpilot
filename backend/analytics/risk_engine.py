"""
Risk Assessment Engine

Calculates stockout and overstock risk based on:
- Current inventory levels
- Forecasted demand
- Supplier lead time
- Dynamic reorder points

Provides risk levels and recommended actions.
All calculations are deterministic.
"""

import numpy as np
from typing import Dict, List, Optional
from analytics.forecaster import forecast_demand
from analytics.reorder_calculator import calculate_dynamic_reorder_point


def calculate_days_until_stockout(
    current_inventory: int,
    forecasted_daily_demand: List[float]
) -> Dict:
    """
    Calculate how many days until inventory runs out.

    Args:
        current_inventory: Current stock level
        forecasted_daily_demand: List of forecasted daily demand

    Returns:
        Days until stockout and cumulative demand tracking
    """
    if current_inventory <= 0:
        return {
            'days_until_stockout': 0.0,
            'already_stockout': True,
            'cumulative_demand': []
        }

    cumulative_demand = 0.0
    cumulative_demands = []

    for day, demand in enumerate(forecasted_daily_demand, start=1):
        cumulative_demand += demand
        cumulative_demands.append(round(cumulative_demand, 2))

        if cumulative_demand >= current_inventory:
            # Interpolate to get fractional day
            prev_cumulative = cumulative_demand - demand
            fraction = (current_inventory - prev_cumulative) / demand if demand > 0 else 0
            days_until_stockout = day - 1 + fraction
            return {
                'days_until_stockout': round(days_until_stockout, 2),
                'already_stockout': False,
                'cumulative_demand': cumulative_demands
            }

    # Inventory lasts beyond forecast horizon
    return {
        'days_until_stockout': len(forecasted_daily_demand),
        'beyond_horizon': True,
        'cumulative_demand': cumulative_demands
    }


def assess_stockout_risk(
    current_inventory: int,
    sales_data: List[float],
    supplier_lead_time_days: int,
    dynamic_reorder_point: Optional[float] = None,
    forecast_horizon_days: int = 30
) -> Dict:
    """
    Assess stockout risk for a SKU.

    Args:
        current_inventory: Current stock level
        sales_data: Historical demand data
        supplier_lead_time_days: Supplier lead time
        dynamic_reorder_point: Pre-calculated dynamic ROP (optional)
        forecast_horizon_days: Forecast horizon

    Returns:
        Complete risk assessment:
        {
            'risk_level': str,  # critical, high, medium, low
            'days_until_stockout': float,
            'stockout_probability': float,
            'recommended_action': str,
            'urgency': str,
            'explanation': str
        }
    """
    if not sales_data or len(sales_data) < 7:
        return {
            'risk_level': 'unknown',
            'error': 'Insufficient data for risk assessment'
        }

    # Get forecast
    forecast_result = forecast_demand(
        sales_data=sales_data,
        forecast_horizon_days=forecast_horizon_days,
        moving_avg_window=14,
        include_trend=True,
        include_seasonality=True
    )

    if 'error' in forecast_result:
        return {
            'risk_level': 'unknown',
            'error': forecast_result['error']
        }

    forecasts = forecast_result['forecasts']

    # Calculate days until stockout
    stockout_calc = calculate_days_until_stockout(
        current_inventory=current_inventory,
        forecasted_daily_demand=forecasts
    )

    days_until_stockout = stockout_calc.get('days_until_stockout', 0.0)
    already_stockout = stockout_calc.get('already_stockout', False)

    # Calculate stockout probability based on days until stockout vs lead time
    # Critical if stockout predicted within lead time
    # High if stockout predicted within 1.5x lead time
    # Medium if within 2x lead time
    # Low otherwise

    if already_stockout:
        stockout_probability = 1.0
        risk_level = 'critical'
        urgency = 'immediate'
        recommended_action = 'emergency_replenishment'
        explanation = "Already in stockout condition. Immediate action required."

    elif days_until_stockout <= supplier_lead_time_days:
        # Stockout predicted before supplier can deliver
        stockout_probability = 0.9
        risk_level = 'critical'
        urgency = 'immediate'
        recommended_action = 'generate_purchase_order'
        explanation = (
            f"Stockout predicted in {days_until_stockout:.1f} days, "
            f"but supplier lead time is {supplier_lead_time_days} days. "
            f"Immediate replenishment required."
        )

    elif days_until_stockout <= supplier_lead_time_days * 1.5:
        stockout_probability = 0.6
        risk_level = 'high'
        urgency = 'urgent'
        recommended_action = 'generate_purchase_order'
        explanation = (
            f"Stockout predicted in {days_until_stockout:.1f} days. "
            f"With {supplier_lead_time_days}-day lead time, replenishment should begin soon."
        )

    elif days_until_stockout <= supplier_lead_time_days * 2:
        stockout_probability = 0.3
        risk_level = 'medium'
        urgency = 'moderate'
        recommended_action = 'monitor_closely'
        explanation = (
            f"Stockout predicted in {days_until_stockout:.1f} days. "
            f"Monitor closely and prepare for replenishment."
        )

    else:
        stockout_probability = 0.1
        risk_level = 'low'
        urgency = 'low'
        recommended_action = 'continue_monitoring'
        explanation = (
            f"Inventory sufficient for {days_until_stockout:.1f} days. "
            f"Continue monitoring."
        )

    # Check against dynamic reorder point if provided
    below_reorder_point = False
    if dynamic_reorder_point is not None:
        below_reorder_point = current_inventory <= dynamic_reorder_point
        if below_reorder_point and risk_level == 'low':
            # Upgrade risk if below dynamic ROP
            risk_level = 'medium'
            urgency = 'moderate'
            recommended_action = 'generate_purchase_order'
            explanation += f" However, inventory is below dynamic reorder point ({dynamic_reorder_point:.0f} units)."

    return {
        'risk_level': risk_level,
        'days_until_stockout': days_until_stockout,
        'stockout_probability': round(stockout_probability, 3),
        'recommended_action': recommended_action,
        'urgency': urgency,
        'current_inventory': current_inventory,
        'supplier_lead_time_days': supplier_lead_time_days,
        'dynamic_reorder_point': dynamic_reorder_point,
        'below_reorder_point': below_reorder_point,
        'explanation': explanation,
        'forecast_confidence': forecast_result['confidence_level']
    }


def assess_overstock_risk(
    current_inventory: int,
    recent_average_demand: float,
    target_inventory_level: float,
    overstock_threshold_multiplier: float = 2.0
) -> Dict:
    """
    Assess overstock risk.

    Args:
        current_inventory: Current stock level
        recent_average_demand: Recent average daily demand
        target_inventory_level: Target/optimal inventory level
        overstock_threshold_multiplier: Multiplier for overstock threshold

    Returns:
        Overstock risk assessment
    """
    if recent_average_demand <= 0:
        return {
            'overstock_risk': 'unknown',
            'error': 'Invalid demand data'
        }

    # Days of inventory on hand
    days_of_inventory = current_inventory / recent_average_demand

    # Overstock threshold (e.g., 2x target level)
    overstock_threshold = target_inventory_level * overstock_threshold_multiplier

    if current_inventory > overstock_threshold:
        overstock_risk = 'high'
        explanation = (
            f"Current inventory ({current_inventory} units) is {current_inventory - overstock_threshold:.0f} units "
            f"above overstock threshold ({overstock_threshold:.0f}). "
            f"Represents {days_of_inventory:.1f} days of inventory."
        )
        recommended_action = 'reduce_procurement'
    elif current_inventory > target_inventory_level * 1.5:
        overstock_risk = 'medium'
        explanation = (
            f"Inventory is elevated but within acceptable range. "
            f"Represents {days_of_inventory:.1f} days of inventory."
        )
        recommended_action = 'monitor'
    else:
        overstock_risk = 'low'
        explanation = (
            f"Inventory level is healthy. "
            f"Represents {days_of_inventory:.1f} days of inventory."
        )
        recommended_action = 'continue_normal_operations'

    return {
        'overstock_risk': overstock_risk,
        'current_inventory': current_inventory,
        'days_of_inventory': round(days_of_inventory, 1),
        'target_inventory_level': round(target_inventory_level, 0),
        'overstock_threshold': round(overstock_threshold, 0),
        'recommended_action': recommended_action,
        'explanation': explanation
    }


def comprehensive_risk_assessment(
    sku_id: str,
    current_inventory: int,
    sales_data: List[float],
    supplier_lead_time_days: int,
    service_level: float = 0.95
) -> Dict:
    """
    Perform comprehensive risk assessment combining stockout and overstock analysis.

    This is the complete risk picture for a SKU.

    Args:
        sku_id: SKU identifier
        current_inventory: Current stock level
        sales_data: Historical demand data
        supplier_lead_time_days: Supplier lead time
        service_level: Target service level

    Returns:
        Complete risk assessment with recommendations
    """
    # Calculate dynamic reorder point
    rop_calc = calculate_dynamic_reorder_point(
        sales_data=sales_data,
        supplier_lead_time_days=supplier_lead_time_days,
        service_level=service_level
    )

    if 'error' in rop_calc:
        return {
            'sku_id': sku_id,
            'error': rop_calc['error'],
            'risk_level': 'unknown'
        }

    dynamic_rop = rop_calc['dynamic_reorder_point']
    recent_avg_demand = rop_calc['avg_daily_demand']

    # Assess stockout risk
    stockout_assessment = assess_stockout_risk(
        current_inventory=current_inventory,
        sales_data=sales_data,
        supplier_lead_time_days=supplier_lead_time_days,
        dynamic_reorder_point=dynamic_rop,
        forecast_horizon_days=30
    )

    # Assess overstock risk
    overstock_assessment = assess_overstock_risk(
        current_inventory=current_inventory,
        recent_average_demand=recent_avg_demand,
        target_inventory_level=dynamic_rop * 1.5  # Target = 1.5x ROP
    )

    # Primary risk is stockout (more critical)
    primary_risk = stockout_assessment['risk_level']
    recommended_action = stockout_assessment['recommended_action']

    return {
        'sku_id': sku_id,
        'overall_risk_level': primary_risk,
        'recommended_action': recommended_action,
        'stockout_assessment': stockout_assessment,
        'overstock_assessment': overstock_assessment,
        'dynamic_reorder_point': dynamic_rop,
        'current_inventory': current_inventory,
        'recent_average_demand': recent_avg_demand,
        'supplier_lead_time_days': supplier_lead_time_days
    }


def generate_risk_summary(risk_assessment: Dict) -> str:
    """
    Generate human-readable risk summary.

    Args:
        risk_assessment: Output from comprehensive_risk_assessment()

    Returns:
        Human-readable summary
    """
    if 'error' in risk_assessment:
        return f"Risk Assessment Error: {risk_assessment['error']}"

    sku_id = risk_assessment['sku_id']
    risk_level = risk_assessment['overall_risk_level']
    action = risk_assessment['recommended_action']
    stockout = risk_assessment['stockout_assessment']

    risk_emoji = {
        'critical': '[CRITICAL]',
        'high': '[HIGH]',
        'medium': '[MEDIUM]',
        'low': '[LOW]'
    }.get(risk_level, '')

    summary = (
        f"{risk_emoji} SKU {sku_id}: {risk_level.upper()} risk. "
        f"{stockout['explanation']} "
        f"Recommended action: {action.replace('_', ' ')}."
    )

    return summary


# Example usage and testing
if __name__ == "__main__":
    print("="*70)
    print("RISK ASSESSMENT ENGINE - TEST")
    print("="*70)

    # Generate sample data mimicking demand spike scenario
    np.random.seed(42)
    days_history = 60
    base_demand = 20
    historical_data = [base_demand + i * 0.5 + np.random.normal(0, 2) for i in range(days_history)]

    print("\nTest 1: Assess Risk for Current Inventory = 184 units")
    print("-" * 70)

    risk_assessment = comprehensive_risk_assessment(
        sku_id="SKU-004",
        current_inventory=184,
        sales_data=historical_data,
        supplier_lead_time_days=7,
        service_level=0.95
    )

    print(generate_risk_summary(risk_assessment))
    print(f"\nDetails:")
    print(f"  Days until stockout: {risk_assessment['stockout_assessment']['days_until_stockout']:.1f}")
    print(f"  Stockout probability: {risk_assessment['stockout_assessment']['stockout_probability']:.1%}")
    print(f"  Dynamic ROP: {risk_assessment['dynamic_reorder_point']:.0f} units")
    print(f"  Below ROP: {risk_assessment['stockout_assessment']['below_reorder_point']}")

    print("\nTest 2: Compare Different Inventory Levels")
    print("-" * 70)

    for inventory_level in [100, 200, 400]:
        risk = assess_stockout_risk(
            current_inventory=inventory_level,
            sales_data=historical_data,
            supplier_lead_time_days=7
        )
        print(f"Inventory={inventory_level}: {risk['risk_level'].upper()} "
              f"(stockout in {risk['days_until_stockout']:.1f} days)")

    print("\n" + "="*70)
