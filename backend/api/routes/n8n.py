"""
n8n Integration API Routes

Endpoints designed for n8n workflow automation:
- Workflow 1: Inventory sync (read/write inventory)
- Workflow 2: Sales data import (bulk insert sales)
- Workflow 3: Automated reorder alerts (check all SKUs, generate POs)
"""

from typing import List, Optional
from datetime import date as date_type
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from models.database import get_db
from models import SKU, Inventory, SalesHistory, SKUSupplier, Supplier, PurchaseOrder
from workflows.procurement_workflow import ProcurementWorkflow
from api.utils import convert_numpy_types


router = APIRouter(prefix="/n8n", tags=["n8n"])


# === Request Models ===

class InventoryUpdate(BaseModel):
    sku_id: str
    current_stock: int

class BulkInventoryUpdate(BaseModel):
    updates: List[InventoryUpdate]

class SalesRecord(BaseModel):
    sku_id: str
    date: str  # YYYY-MM-DD
    quantity_sold: int

class BulkSalesImport(BaseModel):
    records: List[SalesRecord]


# === WORKFLOW 1: Inventory Sync ===

@router.get("/inventory")
async def n8n_get_inventory(db: Session = Depends(get_db)):
    """
    Get all inventory data for n8n sync.
    Returns flat, simple structure optimized for n8n.
    """
    results = db.query(Inventory, SKU).join(SKU, Inventory.sku_id == SKU.id).all()

    return [
        {
            "sku_id": inv.sku_id,
            "product_name": sku.name,
            "category": sku.category,
            "current_stock": inv.current_stock,
            "safety_stock": inv.safety_stock,
            "reorder_point": inv.reorder_point,
            "last_updated": inv.last_updated.isoformat() if inv.last_updated else None
        }
        for inv, sku in results
    ]


@router.put("/inventory/{sku_id}")
async def n8n_update_inventory(
    sku_id: str,
    current_stock: int,
    db: Session = Depends(get_db)
):
    """
    Update stock level for a single SKU.
    Used by n8n Workflow 1 after reading from external source.
    """
    inv = db.query(Inventory).filter(Inventory.sku_id == sku_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail=f"Inventory not found for {sku_id}")

    inv.current_stock = current_stock
    db.commit()
    db.refresh(inv)

    return {"status": "updated", "sku_id": sku_id, "current_stock": inv.current_stock}


@router.put("/inventory/bulk")
async def n8n_bulk_update_inventory(
    payload: BulkInventoryUpdate,
    db: Session = Depends(get_db)
):
    """
    Bulk update inventory levels.
    Used by n8n Workflow 1 to sync multiple SKUs at once.
    """
    updated = []
    errors = []

    for item in payload.updates:
        inv = db.query(Inventory).filter(Inventory.sku_id == item.sku_id).first()
        if inv:
            inv.current_stock = item.current_stock
            updated.append(item.sku_id)
        else:
            errors.append(f"{item.sku_id}: not found")

    db.commit()

    return {
        "status": "complete",
        "updated_count": len(updated),
        "updated_skus": updated,
        "errors": errors
    }


# === WORKFLOW 2: Sales Data Import ===

@router.get("/sales/{sku_id}")
async def n8n_get_sales(
    sku_id: str,
    days: int = 60,
    db: Session = Depends(get_db)
):
    """
    Get recent sales data for a SKU.
    Used by n8n Workflow 2 to check existing data before import.
    """
    from datetime import timedelta
    end = date_type.today()
    start = end - timedelta(days=days)

    sales = db.query(SalesHistory).filter(
        SalesHistory.sku_id == sku_id,
        SalesHistory.date >= start
    ).order_by(SalesHistory.date).all()

    return [
        {
            "sku_id": s.sku_id,
            "date": s.date.isoformat(),
            "quantity_sold": s.quantity_sold
        }
        for s in sales
    ]


@router.post("/sales")
async def n8n_import_sales(
    payload: BulkSalesImport,
    db: Session = Depends(get_db)
):
    """
    Bulk import sales records.
    Used by n8n Workflow 2 to import daily sales data.
    Upserts: if record exists for same sku_id+date, updates quantity.
    """
    imported = 0
    updated = 0
    errors = []

    for rec in payload.records:
        try:
            parsed_date = date_type.fromisoformat(rec.date)
        except ValueError:
            errors.append(f"{rec.sku_id}/{rec.date}: invalid date format")
            continue

        existing = db.query(SalesHistory).filter(
            SalesHistory.sku_id == rec.sku_id,
            SalesHistory.date == parsed_date
        ).first()

        if existing:
            existing.quantity_sold = rec.quantity_sold
            updated += 1
        else:
            new_sale = SalesHistory(
                sku_id=rec.sku_id,
                date=parsed_date,
                quantity_sold=rec.quantity_sold
            )
            db.add(new_sale)
            imported += 1

    db.commit()

    return {
        "status": "complete",
        "imported": imported,
        "updated": updated,
        "total_processed": imported + updated,
        "errors": errors
    }


# === WORKFLOW 3: Automated Reorder Alerts ===

@router.get("/check-reorder")
async def n8n_check_reorder(db: Session = Depends(get_db)):
    """
    Check all SKUs for reorder needs.
    Used by n8n Workflow 3 (scheduled, e.g. every hour).

    Returns only SKUs that need reordering, with full analysis.
    """
    try:
        workflow = ProcurementWorkflow(db)
        decisions = workflow.analyze_all_skus()

        needs_reorder = [d for d in decisions if d.needs_reorder]

        return convert_numpy_types({
            "timestamp": date_type.today().isoformat(),
            "total_skus_checked": len(decisions),
            "reorder_needed": len(needs_reorder),
            "alerts": [
                {
                    "sku_id": d.sku_id,
                    "risk_level": d.risk_assessment.get("risk_level", "unknown"),
                    "reasoning": d.reasoning,
                    "needs_reorder": d.needs_reorder,
                    "recommended_order": d.recommended_order,
                    "forecast": {
                        "method": d.forecast.get("method", ""),
                        "source": d.forecast.get("source", ""),
                        "confidence": d.forecast.get("confidence_level", 0),
                    },
                    "reorder_point": d.reorder_point,
                    "current_stock": d.risk_assessment.get("current_inventory", 0),
                }
                for d in needs_reorder
            ]
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reorder check failed: {str(e)}")


@router.post("/auto-reorder/{sku_id}")
async def n8n_auto_reorder(
    sku_id: str,
    db: Session = Depends(get_db)
):
    """
    Auto-analyze and generate PO for a single SKU.
    Used by n8n Workflow 3 after check-reorder identifies a need.
    """
    try:
        workflow = ProcurementWorkflow(db)
        decision = workflow.analyze_sku(sku_id)

        if not decision.needs_reorder:
            return convert_numpy_types({
                "sku_id": sku_id,
                "po_created": False,
                "message": "No reorder needed",
                "reasoning": decision.reasoning
            })

        if not decision.recommended_order:
            return convert_numpy_types({
                "sku_id": sku_id,
                "po_created": False,
                "message": "Reorder needed but no recommendation generated"
            })

        po = workflow.create_purchase_order(
            sku_id=sku_id,
            supplier_id=decision.recommended_order['supplier_id'],
            quantity=decision.recommended_order['quantity'],
            reasoning=decision.reasoning,
            created_by="n8n_workflow_3"
        )

        return convert_numpy_types({
            "sku_id": sku_id,
            "po_created": True,
            "purchase_order": po.to_dict(),
            "analysis_summary": {
                "risk_level": decision.risk_assessment.get("risk_level", ""),
                "reasoning": decision.reasoning,
                "recommended_quantity": decision.recommended_order['quantity'],
            }
        })

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auto-reorder failed: {str(e)}")


@router.get("/skus")
async def n8n_list_skus(db: Session = Depends(get_db)):
    """
    List all SKU IDs. Helper for n8n workflows that need to iterate.
    """
    skus = db.query(SKU).all()
    return [{"sku_id": s.id, "name": s.name, "category": s.category} for s in skus]


@router.get("/health")
async def n8n_health():
    """
    Health check for n8n to verify API is reachable.
    """
    return {"status": "ok", "service": "stockpilot-n8n-api"}
