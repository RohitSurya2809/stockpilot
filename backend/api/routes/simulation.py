"""
Simulation API Routes

Endpoints for running baseline comparison simulations.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, timedelta

from models import get_db, SKU, Inventory, SalesHistory, SKUSupplier, Supplier
from simulation.scenario_runner import run_comparison_scenario

router = APIRouter()


@router.post("/simulation/run/{sku_id}")
async def run_sku_simulation(
    sku_id: str,
    simulation_days: int = 60,
    fixed_reorder_point: Optional[int] = None,
    fixed_order_quantity: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Run baseline comparison simulation for a SKU.

    Compares StockPilot adaptive strategy vs fixed threshold strategy
    on historical demand data.

    This is CRITICAL for demonstrating quantified improvement.
    """
    # Get SKU
    sku = db.query(SKU).filter(SKU.id == sku_id).first()
    if not sku:
        raise HTTPException(status_code=404, detail=f"SKU {sku_id} not found")

    # Get inventory
    inventory = db.query(Inventory).filter(Inventory.sku_id == sku_id).first()
    if not inventory:
        raise HTTPException(
            status_code=404,
            detail=f"No inventory record for SKU {sku_id}"
        )

    # Get supplier
    sku_supplier = db.query(SKUSupplier, Supplier).join(
        Supplier, SKUSupplier.supplier_id == Supplier.id
    ).filter(
        SKUSupplier.sku_id == sku_id,
        SKUSupplier.is_primary == True
    ).first()

    if not sku_supplier:
        raise HTTPException(
            status_code=404,
            detail=f"No primary supplier found for SKU {sku_id}"
        )

    supplier = sku_supplier[1]

    # Get historical sales data for simulation
    end_date = date.today()
    start_date = end_date - timedelta(days=simulation_days)

    sales = db.query(SalesHistory).filter(
        SalesHistory.sku_id == sku_id,
        SalesHistory.date >= start_date
    ).order_by(SalesHistory.date).all()

    if len(sales) < 30:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient sales data for simulation (need at least 30 days, have {len(sales)})"
        )

    sales_data = [float(s.quantity_sold) for s in sales]

    # Determine initial inventory (use current as baseline)
    initial_inventory = inventory.current_stock

    # Run comparison simulation
    comparison_result = run_comparison_scenario(
        sku_id=sku_id,
        actual_demand_series=sales_data,
        initial_inventory=initial_inventory,
        supplier_lead_time_days=supplier.lead_time_days,
        fixed_reorder_point=fixed_reorder_point,
        fixed_order_quantity=fixed_order_quantity
    )

    # Add product info
    comparison_result['product_name'] = sku.name
    comparison_result['supplier_name'] = supplier.name

    return comparison_result


@router.get("/simulation/comparison")
async def get_all_comparisons(
    simulation_days: int = 60,
    db: Session = Depends(get_db)
):
    """
    Run comparison simulations for all SKUs.

    Returns baseline comparison results for the entire inventory.

    This provides the complete picture for the comparison dashboard.
    """
    # Get all SKUs
    skus = db.query(SKU).all()

    if not skus:
        raise HTTPException(status_code=404, detail="No SKUs found")

    comparisons = []

    for sku in skus:
        try:
            # Get inventory
            inventory = db.query(Inventory).filter(Inventory.sku_id == sku.id).first()
            if not inventory:
                continue

            # Get supplier
            sku_supplier = db.query(SKUSupplier, Supplier).join(
                Supplier, SKUSupplier.supplier_id == Supplier.id
            ).filter(
                SKUSupplier.sku_id == sku.id,
                SKUSupplier.is_primary == True
            ).first()

            if not sku_supplier:
                continue

            supplier = sku_supplier[1]

            # Get historical sales
            end_date = date.today()
            start_date = end_date - timedelta(days=simulation_days)

            sales = db.query(SalesHistory).filter(
                SalesHistory.sku_id == sku.id,
                SalesHistory.date >= start_date
            ).order_by(SalesHistory.date).all()

            if len(sales) < 30:
                continue

            sales_data = [float(s.quantity_sold) for s in sales]

            # Run simulation
            comparison = run_comparison_scenario(
                sku_id=sku.id,
                actual_demand_series=sales_data,
                initial_inventory=inventory.current_stock,
                supplier_lead_time_days=supplier.lead_time_days
            )

            # Add product info
            comparison['product_name'] = sku.name
            comparison['supplier_name'] = supplier.name

            comparisons.append(comparison)

        except Exception as e:
            # Log error but continue with other SKUs
            print(f"Error simulating SKU {sku.id}: {e}")
            continue

    if not comparisons:
        raise HTTPException(
            status_code=400,
            detail="Could not generate comparisons for any SKUs"
        )

    # Calculate aggregate metrics
    total_baseline_stockouts = sum(c['baseline_strategy']['metrics']['stockouts'] for c in comparisons)
    total_adaptive_stockouts = sum(c['adaptive_strategy']['metrics']['stockouts'] for c in comparisons)
    avg_baseline_service = sum(c['baseline_strategy']['metrics']['service_level'] for c in comparisons) / len(comparisons)
    avg_adaptive_service = sum(c['adaptive_strategy']['metrics']['service_level'] for c in comparisons) / len(comparisons)

    return {
        'comparisons': comparisons,
        'aggregate_metrics': {
            'total_skus_compared': len(comparisons),
            'total_baseline_stockouts': total_baseline_stockouts,
            'total_adaptive_stockouts': total_adaptive_stockouts,
            'stockout_reduction': total_baseline_stockouts - total_adaptive_stockouts,
            'avg_baseline_service_level': round(avg_baseline_service, 2),
            'avg_adaptive_service_level': round(avg_adaptive_service, 2),
            'avg_service_level_improvement': round(avg_adaptive_service - avg_baseline_service, 2)
        }
    }
