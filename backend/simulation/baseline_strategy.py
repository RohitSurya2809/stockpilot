"""
Baseline Fixed-Threshold Strategy

Traditional inventory management approach for comparison.

Simple logic:
- If current_stock <= fixed_reorder_point: order fixed_order_quantity
- No intelligence, no pattern awareness, no adaptation

This demonstrates what StockPilot improves upon.
"""

from typing import Dict, List, Tuple


class FixedThresholdStrategy:
    """
    Traditional fixed reorder point strategy.

    Parameters are set once and never change regardless of demand patterns.
    """

    def __init__(
        self,
        sku_id: str,
        fixed_reorder_point: int,
        fixed_order_quantity: int,
        supplier_lead_time_days: int
    ):
        """
        Initialize fixed threshold strategy.

        Args:
            sku_id: SKU identifier
            fixed_reorder_point: Static reorder point (never changes)
            fixed_order_quantity: Static order quantity (never changes)
            supplier_lead_time_days: Supplier lead time
        """
        self.sku_id = sku_id
        self.fixed_reorder_point = fixed_reorder_point
        self.fixed_order_quantity = fixed_order_quantity
        self.supplier_lead_time_days = supplier_lead_time_days

        # Metrics tracking
        self.orders_placed = []
        self.stockouts = 0
        self.overstock_events = 0
        self.emergency_orders = 0

    def check_reorder_condition(
        self,
        current_inventory: int,
        current_day: int
    ) -> Tuple[bool, Dict]:
        """
        Check if reorder is needed based on fixed threshold.

        Simple logic: if inventory <= threshold, order.

        Args:
            current_inventory: Current stock level
            current_day: Current simulation day

        Returns:
            Tuple of (should_reorder, order_details)
        """
        should_reorder = current_inventory <= self.fixed_reorder_point

        if should_reorder:
            order_details = {
                'day': current_day,
                'quantity': self.fixed_order_quantity,
                'reason': f'Inventory ({current_inventory}) at or below fixed threshold ({self.fixed_reorder_point})',
                'reorder_point_used': self.fixed_reorder_point,
                'emergency': current_inventory <= self.fixed_reorder_point * 0.5  # Very low
            }

            # Track emergency orders
            if order_details['emergency']:
                self.emergency_orders += 1

            self.orders_placed.append(order_details)

            return True, order_details
        else:
            return False, {}

    def get_strategy_info(self) -> Dict:
        """Get strategy configuration info."""
        return {
            'strategy_type': 'fixed_threshold',
            'sku_id': self.sku_id,
            'fixed_reorder_point': self.fixed_reorder_point,
            'fixed_order_quantity': self.fixed_order_quantity,
            'supplier_lead_time_days': self.supplier_lead_time_days
        }

    def get_metrics(self) -> Dict:
        """Get strategy performance metrics."""
        return {
            'orders_placed': len(self.orders_placed),
            'stockouts': self.stockouts,
            'overstock_events': self.overstock_events,
            'emergency_orders': self.emergency_orders,
            'order_details': self.orders_placed
        }

    def reset_metrics(self):
        """Reset metrics for new simulation."""
        self.orders_placed = []
        self.stockouts = 0
        self.overstock_events = 0
        self.emergency_orders = 0


# Helper function for creating baseline strategies with typical parameters
def create_baseline_strategy(
    sku_id: str,
    historical_demand: List[float],
    supplier_lead_time_days: int
) -> FixedThresholdStrategy:
    """
    Create a baseline strategy with typical fixed parameters.

    Uses simple heuristics based on historical average:
    - Fixed ROP = avg_demand * lead_time * 1.5
    - Fixed order qty = avg_demand * lead_time * 2

    Args:
        sku_id: SKU identifier
        historical_demand: Historical demand data (to calculate initial parameters)
        supplier_lead_time_days: Supplier lead time

    Returns:
        Configured FixedThresholdStrategy
    """
    import numpy as np

    avg_demand = np.mean(historical_demand) if historical_demand else 50

    # Simple fixed parameters
    # These don't change even if demand pattern changes
    fixed_rop = int(avg_demand * supplier_lead_time_days * 1.5)
    fixed_qty = int(avg_demand * supplier_lead_time_days * 2)

    return FixedThresholdStrategy(
        sku_id=sku_id,
        fixed_reorder_point=fixed_rop,
        fixed_order_quantity=fixed_qty,
        supplier_lead_time_days=supplier_lead_time_days
    )


# Example usage
if __name__ == "__main__":
    print("="*70)
    print("BASELINE FIXED-THRESHOLD STRATEGY - TEST")
    print("="*70)

    # Create strategy
    strategy = FixedThresholdStrategy(
        sku_id="SKU-TEST",
        fixed_reorder_point=100,
        fixed_order_quantity=300,
        supplier_lead_time_days=7
    )

    print("\nStrategy Configuration:")
    print("-" * 70)
    info = strategy.get_strategy_info()
    for key, value in info.items():
        print(f"  {key}: {value}")

    print("\nSimulation Test:")
    print("-" * 70)

    # Simulate inventory levels
    test_inventories = [150, 120, 100, 95, 80, 200, 90]

    for day, inventory in enumerate(test_inventories, start=1):
        should_order, order_details = strategy.check_reorder_condition(inventory, day)
        print(f"Day {day}: Inventory={inventory} -> Order: {should_order}", end="")
        if should_order:
            print(f" (Qty: {order_details['quantity']}, Emergency: {order_details['emergency']})")
        else:
            print()

    print("\nFinal Metrics:")
    print("-" * 70)
    metrics = strategy.get_metrics()
    print(f"  Orders placed: {metrics['orders_placed']}")
    print(f"  Emergency orders: {metrics['emergency_orders']}")

    print("\n" + "="*70)
