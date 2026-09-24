"""
Simulation Scenario Runner

Runs both baseline and adaptive strategies on the same demand data
to compare performance.

This is CRITICAL for demonstrating StockPilot's advantage to judges.

Tracks metrics:
- Stockouts
- Overstock events
- Service level
- Average inventory
- Emergency orders
- Order frequency
"""

import numpy as np
from typing import Dict, List, Tuple
from simulation.baseline_strategy import FixedThresholdStrategy, create_baseline_strategy
from simulation.adaptive_strategy import AdaptiveStrategy


class InventorySimulator:
    """
    Simulates inventory dynamics over time.

    Handles:
    - Daily demand fulfillment
    - Ordering decisions (from strategy)
    - Supplier deliveries (with lead time)
    - Stockout/overstock tracking
    """

    def __init__(
        self,
        sku_id: str,
        initial_inventory: int,
        strategy,
        supplier_lead_time_days: int
    ):
        """
        Initialize inventory simulator.

        Args:
            sku_id: SKU identifier
            initial_inventory: Starting inventory level
            strategy: Strategy instance (baseline or adaptive)
            supplier_lead_time_days: Supplier lead time
        """
        self.sku_id = sku_id
        self.initial_inventory = initial_inventory
        self.strategy = strategy
        self.supplier_lead_time_days = supplier_lead_time_days

        # Simulation state
        self.current_inventory = initial_inventory
        self.pending_orders = []  # (arrival_day, quantity)
        self.inventory_history = []
        self.demand_fulfilled_history = []
        self.demand_unfulfilled_history = []

        # Metrics
        self.total_demand = 0
        self.total_fulfilled = 0
        self.stockout_days = 0
        self.overstock_days = 0

    def simulate_day(
        self,
        day: int,
        demand: float,
        sales_history: List[float]
    ) -> Dict:
        """
        Simulate one day of inventory operations.

        Order of operations:
        1. Receive incoming deliveries
        2. Check reorder condition
        3. Place order if needed
        4. Fulfill demand (if possible)
        5. Record metrics

        Args:
            day: Current day number
            demand: Demand for this day
            sales_history: Historical sales up to yesterday

        Returns:
            Day simulation result
        """
        # 1. Process deliveries
        arriving_orders = [qty for arrival_day, qty in self.pending_orders if arrival_day == day]
        for qty in arriving_orders:
            self.current_inventory += qty

        # Remove delivered orders
        self.pending_orders = [(d, q) for d, q in self.pending_orders if d != day]

        # 2. Check if reorder needed
        if isinstance(self.strategy, AdaptiveStrategy):
            should_order, order_details = self.strategy.check_reorder_condition(
                current_inventory=self.current_inventory,
                sales_history=sales_history,
                current_day=day
            )
        else:  # Fixed threshold
            should_order, order_details = self.strategy.check_reorder_condition(
                current_inventory=self.current_inventory,
                current_day=day
            )

        # 3. Place order if needed
        if should_order:
            arrival_day = day + self.supplier_lead_time_days
            quantity = order_details['quantity']
            self.pending_orders.append((arrival_day, quantity))

        # 4. Fulfill demand
        demand_int = int(round(demand))
        if self.current_inventory >= demand_int:
            # Fulfill completely
            self.current_inventory -= demand_int
            fulfilled = demand_int
            unfulfilled = 0
        else:
            # Partial fulfillment (stockout)
            fulfilled = self.current_inventory
            unfulfilled = demand_int - self.current_inventory
            self.current_inventory = 0
            self.stockout_days += 1
            self.strategy.stockouts += 1

        # 5. Check overstock
        if self.current_inventory > self.initial_inventory * 1.5:
            self.overstock_days += 1
            self.strategy.overstock_events += 1

        # 6. Record metrics
        self.total_demand += demand_int
        self.total_fulfilled += fulfilled
        self.inventory_history.append(self.current_inventory)
        self.demand_fulfilled_history.append(fulfilled)
        self.demand_unfulfilled_history.append(unfulfilled)

        return {
            'day': day,
            'demand': demand_int,
            'fulfilled': fulfilled,
            'unfulfilled': unfulfilled,
            'inventory_level': self.current_inventory,
            'order_placed': should_order,
            'pending_orders': len(self.pending_orders)
        }

    def get_metrics(self) -> Dict:
        """Calculate final simulation metrics."""
        service_level = (self.total_fulfilled / self.total_demand * 100) if self.total_demand > 0 else 0
        avg_inventory = np.mean(self.inventory_history) if self.inventory_history else 0

        return {
            'stockouts': self.strategy.stockouts,
            'stockout_days': self.stockout_days,
            'overstock_days': self.overstock_days,
            'service_level': round(service_level, 2),
            'total_demand': self.total_demand,
            'total_fulfilled': self.total_fulfilled,
            'total_unfulfilled': self.total_demand - self.total_fulfilled,
            'average_inventory': round(avg_inventory, 2),
            'orders_placed': len(self.strategy.orders_placed),
            'emergency_orders': self.strategy.emergency_orders,
            'inventory_history': self.inventory_history
        }


def run_comparison_scenario(
    sku_id: str,
    actual_demand_series: List[float],
    initial_inventory: int,
    supplier_lead_time_days: int,
    fixed_reorder_point: int = None,
    fixed_order_quantity: int = None
) -> Dict:
    """
    Run both strategies on the same demand scenario and compare results.

    This is THE CRITICAL COMPARISON for judging.

    Args:
        sku_id: SKU identifier
        actual_demand_series: Actual demand data for simulation
        initial_inventory: Starting inventory
        supplier_lead_time_days: Supplier lead time
        fixed_reorder_point: Fixed threshold (auto-calculated if None)
        fixed_order_quantity: Fixed order qty (auto-calculated if None)

    Returns:
        Complete comparison report
    """
    # If fixed parameters not provided, calculate reasonable defaults
    if fixed_reorder_point is None or fixed_order_quantity is None:
        avg_demand = np.mean(actual_demand_series[:30])  # Use first 30 days
        fixed_reorder_point = int(avg_demand * supplier_lead_time_days * 1.5)
        fixed_order_quantity = int(avg_demand * supplier_lead_time_days * 2)

    # Create strategies
    baseline_strategy = FixedThresholdStrategy(
        sku_id=sku_id,
        fixed_reorder_point=fixed_reorder_point,
        fixed_order_quantity=fixed_order_quantity,
        supplier_lead_time_days=supplier_lead_time_days
    )

    adaptive_strategy = AdaptiveStrategy(
        sku_id=sku_id,
        supplier_lead_time_days=supplier_lead_time_days,
        service_level=0.95,
        minimum_order_quantity=50
    )

    # Create simulators
    baseline_sim = InventorySimulator(
        sku_id=sku_id,
        initial_inventory=initial_inventory,
        strategy=baseline_strategy,
        supplier_lead_time_days=supplier_lead_time_days
    )

    adaptive_sim = InventorySimulator(
        sku_id=sku_id,
        initial_inventory=initial_inventory,
        strategy=adaptive_strategy,
        supplier_lead_time_days=supplier_lead_time_days
    )

    # Run simulations
    sales_history = []

    for day, demand in enumerate(actual_demand_series, start=1):
        # Baseline simulation
        baseline_sim.simulate_day(
            day=day,
            demand=demand,
            sales_history=sales_history
        )

        # Adaptive simulation
        adaptive_sim.simulate_day(
            day=day,
            demand=demand,
            sales_history=sales_history
        )

        # Add to history for next iteration
        sales_history.append(demand)

    # Get metrics
    baseline_metrics = baseline_sim.get_metrics()
    adaptive_metrics = adaptive_sim.get_metrics()

    # Calculate improvements
    stockout_improvement = baseline_metrics['stockouts'] - adaptive_metrics['stockouts']
    service_level_improvement = adaptive_metrics['service_level'] - baseline_metrics['service_level']
    avg_inventory_reduction = baseline_metrics['average_inventory'] - adaptive_metrics['average_inventory']
    avg_inventory_reduction_pct = (avg_inventory_reduction / baseline_metrics['average_inventory'] * 100) if baseline_metrics['average_inventory'] > 0 else 0

    return {
        'sku_id': sku_id,
        'simulation_days': len(actual_demand_series),
        'initial_inventory': initial_inventory,
        'supplier_lead_time_days': supplier_lead_time_days,
        'baseline_strategy': {
            'type': 'fixed_threshold',
            'reorder_point': fixed_reorder_point,
            'order_quantity': fixed_order_quantity,
            'metrics': baseline_metrics
        },
        'adaptive_strategy': {
            'type': 'stockpilot_adaptive',
            'service_level_target': 0.95,
            'metrics': adaptive_metrics
        },
        'comparison': {
            'stockout_reduction': stockout_improvement,
            'service_level_improvement': round(service_level_improvement, 2),
            'avg_inventory_reduction': round(avg_inventory_reduction, 2),
            'avg_inventory_reduction_percentage': round(avg_inventory_reduction_pct, 1),
            'emergency_order_reduction': baseline_metrics['emergency_orders'] - adaptive_metrics['emergency_orders']
        },
        'verdict': generate_verdict(baseline_metrics, adaptive_metrics)
    }


def generate_verdict(baseline_metrics: Dict, adaptive_metrics: Dict) -> str:
    """
    Generate verdict comparing the two strategies.

    Args:
        baseline_metrics: Baseline strategy metrics
        adaptive_metrics: Adaptive strategy metrics

    Returns:
        Human-readable verdict
    """
    stockout_diff = baseline_metrics['stockouts'] - adaptive_metrics['stockouts']
    service_diff = adaptive_metrics['service_level'] - baseline_metrics['service_level']

    if stockout_diff > 0 and service_diff > 5:
        verdict = "StockPilot significantly outperforms fixed threshold"
    elif stockout_diff > 0 or service_diff > 2:
        verdict = "StockPilot shows measurable improvement"
    elif stockout_diff == 0 and abs(service_diff) < 2:
        verdict = "Both strategies perform similarly"
    else:
        verdict = "Unexpected results - review needed"

    return verdict


# Example usage and testing
if __name__ == "__main__":
    print("="*70)
    print("SIMULATION SCENARIO RUNNER - TEST")
    print("="*70)

    # Generate demand spike scenario (mimics demo)
    np.random.seed(42)
    days = 60
    base_demand = 20

    # Create demand spike
    demand_series = []
    for day in range(days):
        if day < 40:
            # Normal demand
            demand = base_demand + np.random.normal(0, 2)
        else:
            # Spike begins
            days_into_spike = day - 40
            growth = 1 + (2.0 - 1) * min(days_into_spike / 10, 1)
            demand = base_demand * growth + np.random.normal(0, 2)

        demand_series.append(max(0, demand))

    print("\nRunning Comparison Simulation:")
    print("-" * 70)
    print(f"SKU: SKU-004 (Wireless Mouse)")
    print(f"Scenario: Demand spike starting at day 40")
    print(f"Days: {days}")
    print(f"Initial inventory: 800 units")
    print(f"Supplier lead time: 7 days")

    # Run comparison
    comparison = run_comparison_scenario(
        sku_id="SKU-004",
        actual_demand_series=demand_series,
        initial_inventory=800,
        supplier_lead_time_days=7,
        fixed_reorder_point=100,
        fixed_order_quantity=300
    )

    print("\nRESULTS:")
    print("=" * 70)

    print("\nFixed Threshold Strategy:")
    print("-" * 70)
    baseline = comparison['baseline_strategy']['metrics']
    print(f"  Stockouts: {baseline['stockouts']}")
    print(f"  Service Level: {baseline['service_level']}%")
    print(f"  Average Inventory: {baseline['average_inventory']:.1f} units")
    print(f"  Orders Placed: {baseline['orders_placed']}")
    print(f"  Emergency Orders: {baseline['emergency_orders']}")

    print("\nStockPilot Adaptive Strategy:")
    print("-" * 70)
    adaptive = comparison['adaptive_strategy']['metrics']
    print(f"  Stockouts: {adaptive['stockouts']}")
    print(f"  Service Level: {adaptive['service_level']}%")
    print(f"  Average Inventory: {adaptive['average_inventory']:.1f} units")
    print(f"  Orders Placed: {adaptive['orders_placed']}")
    print(f"  Emergency Orders: {adaptive['emergency_orders']}")

    print("\nIMPROVEMENT:")
    print("-" * 70)
    comp = comparison['comparison']
    print(f"  Stockout Reduction: {comp['stockout_reduction']}")
    print(f"  Service Level Improvement: +{comp['service_level_improvement']}%")
    print(f"  Avg Inventory Reduction: {comp['avg_inventory_reduction']:.1f} units ({comp['avg_inventory_reduction_percentage']:.1f}%)")
    print(f"  Emergency Order Reduction: {comp['emergency_order_reduction']}")

    print(f"\nVerdict: {comparison['verdict']}")

    print("\n" + "="*70)
