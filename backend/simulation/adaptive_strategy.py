"""
Adaptive StockPilot Strategy

Intelligent inventory management using:
- Demand pattern analysis
- Forecasting
- Dynamic reorder points
- Risk assessment

This demonstrates StockPilot's intelligence vs fixed thresholds.
"""

from typing import Dict, List, Tuple
from analytics.reorder_calculator import calculate_dynamic_reorder_point, calculate_order_quantity
from analytics.risk_engine import assess_stockout_risk


class AdaptiveStrategy:
    """
    StockPilot's adaptive reorder strategy.

    Dynamically adjusts reorder points based on:
    - Demand patterns
    - Forecasted future demand
    - Supplier lead time
    - Risk assessment
    """

    def __init__(
        self,
        sku_id: str,
        supplier_lead_time_days: int,
        service_level: float = 0.95,
        minimum_order_quantity: int = 1
    ):
        """
        Initialize adaptive strategy.

        Args:
            sku_id: SKU identifier
            supplier_lead_time_days: Supplier lead time
            service_level: Target service level (default: 0.95)
            minimum_order_quantity: Minimum order qty
        """
        self.sku_id = sku_id
        self.supplier_lead_time_days = supplier_lead_time_days
        self.service_level = service_level
        self.minimum_order_quantity = minimum_order_quantity

        # Metrics tracking
        self.orders_placed = []
        self.stockouts = 0
        self.overstock_events = 0
        self.emergency_orders = 0
        self.reorder_point_history = []
        self.last_order_day = -999  # Cooldown tracking

    def check_reorder_condition(
        self,
        current_inventory: int,
        sales_history: List[float],
        current_day: int
    ) -> Tuple[bool, Dict]:
        """
        Check if reorder is needed using intelligent analysis.

        Uses:
        1. Calculate dynamic reorder point from recent sales data
        2. Assess stockout risk
        3. Decide whether to order

        Args:
            current_inventory: Current stock level
            sales_history: Historical demand data up to this point
            current_day: Current simulation day

        Returns:
            Tuple of (should_reorder, order_details)
        """
        # Cooldown: don't order if we ordered within the last few days (unless emergency)
        days_since_last_order = current_day - self.last_order_day

        if len(sales_history) < 2:
            return False, {}

        if len(sales_history) < 7:
            avg_demand = sum(sales_history) / len(sales_history)
            simple_rop = avg_demand * self.supplier_lead_time_days * 1.5
            if current_inventory <= simple_rop and days_since_last_order >= self.supplier_lead_time_days:
                order_qty = int(avg_demand * self.supplier_lead_time_days * 2.5)
                order_qty = max(order_qty, self.minimum_order_quantity)
                self.last_order_day = current_day
                order_details = {
                    'day': current_day,
                    'quantity': order_qty,
                    'reason': 'Warmup period - proactive order based on early demand estimate',
                    'reorder_point_used': simple_rop,
                    'risk_level': 'medium',
                    'days_until_stockout': current_inventory / max(avg_demand, 1),
                    'emergency': False
                }
                self.orders_placed.append(order_details)
                return True, order_details
            return False, {}

        # Calculate dynamic reorder point
        rop_calc = calculate_dynamic_reorder_point(
            sales_data=sales_history,
            supplier_lead_time_days=self.supplier_lead_time_days,
            service_level=self.service_level
        )

        if 'error' in rop_calc:
            return False, {}

        dynamic_rop = rop_calc['dynamic_reorder_point']

        self.reorder_point_history.append({
            'day': current_day,
            'reorder_point': dynamic_rop
        })

        # Assess stockout risk
        risk_assessment = assess_stockout_risk(
            current_inventory=current_inventory,
            sales_data=sales_history,
            supplier_lead_time_days=self.supplier_lead_time_days,
            dynamic_reorder_point=dynamic_rop
        )

        is_emergency = (
            risk_assessment['risk_level'] == 'critical' and
            current_inventory <= dynamic_rop
        )

        # Order when at or approaching dynamic ROP (10% buffer), with cooldown
        cooldown = max(self.supplier_lead_time_days // 2, 2)
        rop_with_buffer = dynamic_rop * 1.1
        should_reorder = (
            current_inventory <= rop_with_buffer and
            (days_since_last_order >= cooldown or is_emergency)
        )

        if should_reorder:
            order_calc = calculate_order_quantity(
                sales_data=sales_history,
                current_inventory=current_inventory,
                dynamic_rop=dynamic_rop,
                supplier_lead_time_days=self.supplier_lead_time_days,
                minimum_order_quantity=self.minimum_order_quantity
            )

            order_quantity = max(order_calc['order_quantity'], self.minimum_order_quantity)

            order_details = {
                'day': current_day,
                'quantity': order_quantity,
                'reason': risk_assessment['explanation'],
                'reorder_point_used': dynamic_rop,
                'risk_level': risk_assessment['risk_level'],
                'days_until_stockout': risk_assessment['days_until_stockout'],
                'emergency': is_emergency
            }

            if is_emergency:
                self.emergency_orders += 1

            self.last_order_day = current_day
            self.orders_placed.append(order_details)

            return True, order_details
        else:
            return False, {}

    def get_strategy_info(self) -> Dict:
        """Get strategy configuration info."""
        return {
            'strategy_type': 'adaptive_stockpilot',
            'sku_id': self.sku_id,
            'supplier_lead_time_days': self.supplier_lead_time_days,
            'service_level': self.service_level,
            'minimum_order_quantity': self.minimum_order_quantity,
            'description': 'Dynamic reorder points based on demand patterns and forecasting'
        }

    def get_metrics(self) -> Dict:
        """Get strategy performance metrics."""
        return {
            'orders_placed': len(self.orders_placed),
            'stockouts': self.stockouts,
            'overstock_events': self.overstock_events,
            'emergency_orders': self.emergency_orders,
            'order_details': self.orders_placed,
            'reorder_point_history': self.reorder_point_history
        }

    def reset_metrics(self):
        """Reset metrics for new simulation."""
        self.orders_placed = []
        self.stockouts = 0
        self.overstock_events = 0
        self.emergency_orders = 0
        self.reorder_point_history = []
        self.last_order_day = -999


# Example usage
if __name__ == "__main__":
    import numpy as np

    print("="*70)
    print("ADAPTIVE STOCKPILOT STRATEGY - TEST")
    print("="*70)

    # Create strategy
    strategy = AdaptiveStrategy(
        sku_id="SKU-TEST",
        supplier_lead_time_days=7,
        service_level=0.95,
        minimum_order_quantity=50
    )

    print("\nStrategy Configuration:")
    print("-" * 70)
    info = strategy.get_strategy_info()
    for key, value in info.items():
        print(f"  {key}: {value}")

    print("\nSimulation Test with Increasing Demand:")
    print("-" * 70)

    # Generate increasing demand pattern
    np.random.seed(42)
    base_demand = 20
    historical_sales = []

    for day in range(1, 31):
        # Simulate increasing demand
        demand = base_demand + day * 0.5 + np.random.normal(0, 2)
        demand = max(0, demand)
        historical_sales.append(demand)

        # Current inventory decreases by demand
        current_inventory = 200 - int(sum(historical_sales[-7:]))  # Last 7 days impact

        # Check if reorder needed
        should_order, order_details = strategy.check_reorder_condition(
            current_inventory=current_inventory,
            sales_history=historical_sales,
            current_day=day
        )

        if should_order:
            print(f"Day {day}: Inventory={current_inventory} -> ORDER "
                  f"(Qty: {order_details['quantity']}, "
                  f"Risk: {order_details['risk_level']}, "
                  f"ROP: {order_details['reorder_point_used']:.0f})")

    print("\nFinal Metrics:")
    print("-" * 70)
    metrics = strategy.get_metrics()
    print(f"  Orders placed: {metrics['orders_placed']}")
    print(f"  Emergency orders: {metrics['emergency_orders']}")

    if metrics['reorder_point_history']:
        print(f"\nReorder Point Evolution:")
        for entry in metrics['reorder_point_history'][:5]:
            print(f"    Day {entry['day']}: ROP = {entry['reorder_point']:.0f} units")

    print("\n" + "="*70)
