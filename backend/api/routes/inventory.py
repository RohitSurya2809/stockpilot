"""
Inventory API Routes

Endpoints for querying inventory, SKU, and sales history data.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List
from datetime import date, timedelta

from models import get_db, SKU, Inventory, SalesHistory, SKUSupplier, Supplier
from api.schemas.inventory_schema import (
    SKUResponse,
    InventoryResponse,
    SalesHistoryResponse,
    InventorySummaryResponse
)

router = APIRouter()


@router.get("/inventory", response_model=List[InventorySummaryResponse])
async def get_all_inventory(
    db: Session = Depends(get_db),
    include_risk: bool = False
):
    """
    Get all SKUs with their current inventory levels.

    Args:
        include_risk: If True, include calculated risk information (slower)

    Returns:
        List of inventory summaries
    """
    skus = db.query(SKU).all()
    summaries = []

    for sku in skus:
        # Get inventory
        inventory = db.query(Inventory).filter(Inventory.sku_id == sku.id).first()
        if not inventory:
            continue

        # Get primary supplier
        sku_supplier = db.query(SKUSupplier, Supplier).join(
            Supplier, SKUSupplier.supplier_id == Supplier.id
        ).filter(
            SKUSupplier.sku_id == sku.id,
            SKUSupplier.is_primary == True
        ).first()

        supplier_name = sku_supplier[1].name if sku_supplier else None
        supplier_lead_time = sku_supplier[1].lead_time_days if sku_supplier else None

        # Calculate recent daily demand (last 7 days)
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        recent_sales = db.query(func.avg(SalesHistory.quantity_sold)).filter(
            SalesHistory.sku_id == sku.id,
            SalesHistory.date >= start_date,
            SalesHistory.date <= end_date
        ).scalar()

        summary = InventorySummaryResponse(
            sku_id=sku.id,
            product_name=sku.name,
            category=sku.category,
            current_stock=inventory.current_stock,
            safety_stock=inventory.safety_stock,
            reorder_point=inventory.reorder_point,
            recent_daily_demand=float(recent_sales) if recent_sales else None,
            supplier_name=supplier_name,
            supplier_lead_time=supplier_lead_time,
            demand_trend=None,  # Will be calculated by analytics engine
            risk_level=None,     # Will be calculated by analytics engine
            days_until_stockout=None
        )
        summaries.append(summary)

    return summaries


@router.get("/inventory/{sku_id}", response_model=InventorySummaryResponse)
async def get_sku_inventory(
    sku_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed inventory information for a specific SKU.

    Args:
        sku_id: SKU identifier

    Returns:
        Inventory summary for the SKU
    """
    # Get SKU
    sku = db.query(SKU).filter(SKU.id == sku_id).first()
    if not sku:
        raise HTTPException(status_code=404, detail=f"SKU {sku_id} not found")

    # Get inventory
    inventory = db.query(Inventory).filter(Inventory.sku_id == sku_id).first()
    if not inventory:
        raise HTTPException(status_code=404, detail=f"No inventory record for SKU {sku_id}")

    # Get primary supplier
    sku_supplier = db.query(SKUSupplier, Supplier).join(
        Supplier, SKUSupplier.supplier_id == Supplier.id
    ).filter(
        SKUSupplier.sku_id == sku_id,
        SKUSupplier.is_primary == True
    ).first()

    supplier_name = sku_supplier[1].name if sku_supplier else None
    supplier_lead_time = sku_supplier[1].lead_time_days if sku_supplier else None

    # Calculate recent daily demand
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    recent_sales = db.query(func.avg(SalesHistory.quantity_sold)).filter(
        SalesHistory.sku_id == sku_id,
        SalesHistory.date >= start_date,
        SalesHistory.date <= end_date
    ).scalar()

    return InventorySummaryResponse(
        sku_id=sku.id,
        product_name=sku.name,
        category=sku.category,
        current_stock=inventory.current_stock,
        safety_stock=inventory.safety_stock,
        reorder_point=inventory.reorder_point,
        recent_daily_demand=float(recent_sales) if recent_sales else None,
        supplier_name=supplier_name,
        supplier_lead_time=supplier_lead_time
    )


@router.get("/sales-history/{sku_id}", response_model=List[SalesHistoryResponse])
async def get_sales_history(
    sku_id: str,
    days: int = 90,
    db: Session = Depends(get_db)
):
    """
    Get sales history for a specific SKU.

    Args:
        sku_id: SKU identifier
        days: Number of days of history to retrieve (default: 90)

    Returns:
        List of sales history records
    """
    # Check if SKU exists
    sku = db.query(SKU).filter(SKU.id == sku_id).first()
    if not sku:
        raise HTTPException(status_code=404, detail=f"SKU {sku_id} not found")

    # Get sales history
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    sales = db.query(SalesHistory).filter(
        SalesHistory.sku_id == sku_id,
        SalesHistory.date >= start_date,
        SalesHistory.date <= end_date
    ).order_by(SalesHistory.date).all()

    return [
        SalesHistoryResponse(
            sku_id=sale.sku_id,
            date=sale.date,
            quantity_sold=sale.quantity_sold
        )
        for sale in sales
    ]


@router.get("/skus", response_model=List[SKUResponse])
async def get_all_skus(db: Session = Depends(get_db)):
    """
    Get all SKUs.

    Returns:
        List of all SKUs
    """
    skus = db.query(SKU).all()
    return [
        SKUResponse(
            id=sku.id,
            name=sku.name,
            category=sku.category,
            unit_cost=sku.unit_cost,
            minimum_order_quantity=sku.minimum_order_quantity
        )
        for sku in skus
    ]


@router.get("/skus/{sku_id}", response_model=SKUResponse)
async def get_sku(sku_id: str, db: Session = Depends(get_db)):
    """
    Get a specific SKU.

    Args:
        sku_id: SKU identifier

    Returns:
        SKU information
    """
    sku = db.query(SKU).filter(SKU.id == sku_id).first()
    if not sku:
        raise HTTPException(status_code=404, detail=f"SKU {sku_id} not found")

    return SKUResponse(
        id=sku.id,
        name=sku.name,
        category=sku.category,
        unit_cost=sku.unit_cost,
        minimum_order_quantity=sku.minimum_order_quantity
    )
