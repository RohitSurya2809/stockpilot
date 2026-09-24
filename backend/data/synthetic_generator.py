"""
Synthetic Data Generator for StockPilot

Generates 90 days of realistic inventory and sales data with 6 distinct demand patterns.
"""

import random
from datetime import date, timedelta
from sqlalchemy.orm import Session
from models import (
    SessionLocal, SKU, Inventory, SalesHistory, Supplier, SKUSupplier
)


def generate_stable_demand(base_demand: float, days: int, variance: float = 3.0) -> list:
    """
    Pattern 1: Stable demand with minimal variance.

    Args:
        base_demand: Average daily demand
        days: Number of days to generate
        variance: Standard deviation for random fluctuation

    Returns:
        List of daily demand values
    """
    return [max(0, int(base_demand + random.gauss(0, variance))) for _ in range(days)]


def generate_increasing_demand(start_demand: float, days: int, growth_rate: float = 0.02) -> list:
    """
    Pattern 2: Increasing demand trend.

    Args:
        start_demand: Starting daily demand
        days: Number of days to generate
        growth_rate: Daily growth rate (e.g., 0.02 = 2% per day)

    Returns:
        List of daily demand values
    """
    demands = []
    current = start_demand
    for _ in range(days):
        demands.append(max(0, int(current + random.gauss(0, 2))))
        current *= (1 + growth_rate)
    return demands


def generate_seasonal_demand(base_demand: float, days: int, period: int = 7, amplitude: float = 0.5) -> list:
    """
    Pattern 3: Seasonal/cyclic demand (e.g., weekly pattern).

    Args:
        base_demand: Base daily demand
        days: Number of days to generate
        period: Seasonality period in days (7 = weekly)
        amplitude: Peak multiplier (0.5 = 50% increase at peak)

    Returns:
        List of daily demand values
    """
    import math
    demands = []
    for day in range(days):
        # Sine wave for seasonal pattern
        seasonal_factor = 1 + amplitude * math.sin(2 * math.pi * day / period)
        demand = base_demand * seasonal_factor
        demands.append(max(0, int(demand + random.gauss(0, 2))))
    return demands


def generate_spike_demand(base_demand: float, days: int, spike_day: int = 60, spike_multiplier: float = 3.0) -> list:
    """
    Pattern 4: Demand spike (THIS IS THE DEMO PATTERN).

    Args:
        base_demand: Normal daily demand
        days: Number of days to generate
        spike_day: Day when spike begins
        spike_multiplier: Multiplier for spike intensity

    Returns:
        List of daily demand values
    """
    demands = []
    for day in range(days):
        if day < spike_day:
            # Normal demand before spike
            demand = base_demand
        else:
            # Gradual increase after spike day
            days_since_spike = day - spike_day
            growth = 1 + (spike_multiplier - 1) * min(days_since_spike / 10, 1)
            demand = base_demand * growth

        demands.append(max(0, int(demand + random.gauss(0, 2))))
    return demands


def generate_decreasing_demand(start_demand: float, days: int, decline_rate: float = -0.015) -> list:
    """
    Pattern 5: Decreasing demand trend.

    Args:
        start_demand: Starting daily demand
        days: Number of days to generate
        decline_rate: Daily decline rate (e.g., -0.015 = -1.5% per day)

    Returns:
        List of daily demand values
    """
    demands = []
    current = start_demand
    for _ in range(days):
        demands.append(max(0, int(current + random.gauss(0, 2))))
        current *= (1 + decline_rate)
    return demands


def generate_volatile_demand(base_demand: float, days: int, volatility: float = 15.0) -> list:
    """
    Pattern 6: Highly volatile demand.

    Args:
        base_demand: Average daily demand
        days: Number of days to generate
        volatility: High standard deviation for wild fluctuations

    Returns:
        List of daily demand values
    """
    return [max(0, int(base_demand + random.gauss(0, volatility))) for _ in range(days)]


def create_suppliers(db: Session):
    """Create supplier records."""
    suppliers_data = [
        {"name": "ABC Supplies", "contact_email": "contact@abcsupplies.com", "lead_time_days": 7, "reliability_score": 0.95},
        {"name": "XYZ Corp", "contact_email": "sales@xyzcorp.com", "lead_time_days": 14, "reliability_score": 0.92},
        {"name": "QuickShip Ltd", "contact_email": "orders@quickship.com", "lead_time_days": 3, "reliability_score": 0.88},
        {"name": "BulkGoods Inc", "contact_email": "info@bulkgoods.com", "lead_time_days": 10, "reliability_score": 0.93},
    ]

    suppliers = []
    for data in suppliers_data:
        supplier = Supplier(**data)
        db.add(supplier)
        suppliers.append(supplier)

    db.commit()
    print(f"Created {len(suppliers)} suppliers")
    return suppliers


def create_skus_and_data(db: Session, suppliers: list, days: int = 90):
    """
    Create SKUs with 6 distinct demand patterns and historical sales data.
    """
    start_date = date.today() - timedelta(days=days)

    # Define SKUs with their patterns
    skus_config = [
        {
            "id": "SKU-001",
            "name": "Office Chair",
            "category": "Furniture",
            "unit_cost": 120.00,
            "min_order_qty": 10,
            "pattern_func": lambda: generate_stable_demand(50, days, variance=3),
            "pattern_name": "Stable (50+/-3 units/day)",
            "supplier_idx": 0,  # ABC Supplies
            "initial_stock": 1500,
            "safety_stock": 200,
        },
        {
            "id": "SKU-002",
            "name": "Laptop Stand",
            "category": "Accessories",
            "unit_cost": 35.00,
            "min_order_qty": 20,
            "pattern_func": lambda: generate_increasing_demand(20, days, growth_rate=0.02),
            "pattern_name": "Increasing (20/day, +2% growth)",
            "supplier_idx": 1,  # XYZ Corp
            "initial_stock": 800,
            "safety_stock": 150,
        },
        {
            "id": "SKU-003",
            "name": "Desk Lamp",
            "category": "Lighting",
            "unit_cost": 45.00,
            "min_order_qty": 15,
            "pattern_func": lambda: generate_seasonal_demand(40, days, period=7, amplitude=0.5),
            "pattern_name": "Seasonal (40/day, weekly +50% peaks)",
            "supplier_idx": 2,  # QuickShip Ltd
            "initial_stock": 1200,
            "safety_stock": 180,
        },
        {
            "id": "SKU-004",
            "name": "Wireless Mouse",
            "category": "Accessories",
            "unit_cost": 25.00,
            "min_order_qty": 50,
            "pattern_func": lambda: generate_spike_demand(20, days, spike_day=60, spike_multiplier=2.5),
            "pattern_name": "Spike (20/day -> 2.5x spike at day 60) [DEMO SKU]",
            "supplier_idx": 0,  # ABC Supplies
            "initial_stock": 800,
            "safety_stock": 120,
        },
        {
            "id": "SKU-005",
            "name": "Monitor Stand",
            "category": "Accessories",
            "unit_cost": 55.00,
            "min_order_qty": 10,
            "pattern_func": lambda: generate_decreasing_demand(60, days, decline_rate=-0.015),
            "pattern_name": "Decreasing (60/day, -1.5% decline)",
            "supplier_idx": 3,  # BulkGoods Inc
            "initial_stock": 1800,
            "safety_stock": 150,
        },
        {
            "id": "SKU-006",
            "name": "USB Cable Pack",
            "category": "Accessories",
            "unit_cost": 15.00,
            "min_order_qty": 100,
            "pattern_func": lambda: generate_volatile_demand(40, days, volatility=15),
            "pattern_name": "Volatile (40+/-15 units/day)",
            "supplier_idx": 1,  # XYZ Corp
            "initial_stock": 1500,
            "safety_stock": 200,
        },
    ]

    print(f"\n{'='*70}")
    print(f"Generating {days} days of synthetic data for {len(skus_config)} SKUs")
    print(f"{'='*70}\n")

    for config in skus_config:
        # Create SKU
        sku = SKU(
            id=config["id"],
            name=config["name"],
            category=config["category"],
            unit_cost=config["unit_cost"],
            minimum_order_quantity=config["min_order_qty"]
        )
        db.add(sku)

        print(f"SKU: {config['id']} - {config['name']}")
        print(f"  Pattern: {config['pattern_name']}")

        # Link to supplier
        supplier = suppliers[config["supplier_idx"]]
        sku_supplier = SKUSupplier(
            sku_id=sku.id,
            supplier_id=supplier.id,
            cost_per_unit=config["unit_cost"],
            is_primary=True
        )
        db.add(sku_supplier)

        # Create initial inventory
        inventory = Inventory(
            sku_id=sku.id,
            current_stock=config["initial_stock"],
            safety_stock=config["safety_stock"],
            reorder_point=config["safety_stock"] + 100  # Initial static reorder point
        )
        db.add(inventory)

        # Generate demand pattern
        demand_pattern = config["pattern_func"]()

        # Create sales history
        total_demand = 0
        for day_offset, quantity in enumerate(demand_pattern):
            sales_date = start_date + timedelta(days=day_offset)
            sales = SalesHistory(
                sku_id=sku.id,
                date=sales_date,
                quantity_sold=quantity
            )
            db.add(sales)
            total_demand += quantity

        avg_demand = total_demand / days
        print(f"  Avg Demand: {avg_demand:.1f} units/day")
        print(f"  Total Demand: {total_demand} units over {days} days")
        print(f"  Initial Stock: {config['initial_stock']} units")
        print(f"  Supplier: {supplier.name} (Lead time: {supplier.lead_time_days} days)")
        print()

    db.commit()
    print(f"{'='*70}")
    print(f"Successfully created {len(skus_config)} SKUs with {days} days of sales history")
    print(f"{'='*70}\n")


def verify_data(db: Session):
    """Verify generated data."""
    print("\n" + "="*70)
    print("DATA VERIFICATION")
    print("="*70 + "\n")

    # Count records
    sku_count = db.query(SKU).count()
    inventory_count = db.query(Inventory).count()
    sales_count = db.query(SalesHistory).count()
    supplier_count = db.query(Supplier).count()
    sku_supplier_count = db.query(SKUSupplier).count()

    print(f"[OK] SKUs: {sku_count}")
    print(f"[OK] Inventory records: {inventory_count}")
    print(f"[OK] Sales history records: {sales_count}")
    print(f"[OK] Suppliers: {supplier_count}")
    print(f"[OK] SKU-Supplier links: {sku_supplier_count}")

    # Show sample data for demo SKU (SKU-004)
    demo_sku = db.query(SKU).filter(SKU.id == "SKU-004").first()
    if demo_sku:
        print(f"\n" + "-"*70)
        print(f"DEMO SKU: {demo_sku.id} - {demo_sku.name}")
        print("-"*70)

        # Get last 10 days of sales
        recent_sales = db.query(SalesHistory).filter(
            SalesHistory.sku_id == demo_sku.id
        ).order_by(SalesHistory.date.desc()).limit(10).all()

        print("\nRecent sales (last 10 days):")
        for sale in reversed(recent_sales):
            print(f"  {sale.date}: {sale.quantity_sold} units")

        inventory = db.query(Inventory).filter(Inventory.sku_id == demo_sku.id).first()
        if inventory:
            print(f"\nCurrent inventory: {inventory.current_stock} units")
            print(f"Safety stock: {inventory.safety_stock} units")
            print(f"Reorder point: {inventory.reorder_point} units")

    print("\n" + "="*70 + "\n")


def main():
    """Main function to generate all synthetic data."""
    print("\n" + "="*70)
    print("STOCKPILOT SYNTHETIC DATA GENERATOR")
    print("="*70 + "\n")

    db = SessionLocal()

    try:
        # Check if data already exists
        existing_skus = db.query(SKU).count()
        if existing_skus > 0:
            print(f"[WARNING] WARNING: Database already contains {existing_skus} SKUs")
            response = input("Clear existing data and regenerate? (yes/no): ")
            if response.lower() != 'yes':
                print("Aborted.")
                return

            # Clear existing data
            print("\nClearing existing data...")
            db.query(SalesHistory).delete()
            db.query(SKUSupplier).delete()
            db.query(Inventory).delete()
            db.query(SKU).delete()
            db.query(Supplier).delete()
            db.commit()
            print("[OK] Existing data cleared\n")

        # Generate data
        suppliers = create_suppliers(db)
        create_skus_and_data(db, suppliers, days=90)
        verify_data(db)

        print("[OK] Data generation complete!")
        print("\nYou can now start the StockPilot API and explore the data.\n")

    except Exception as e:
        print(f"\n[ERROR] Error generating data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
