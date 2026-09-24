"""
Procurement API Routes

Endpoints for end-to-end procurement workflow:
- Analyze SKUs for reorder needs
- Generate purchase orders
- Approve/reject purchase orders
- View PO history
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from models.database import get_db
from models import PurchaseOrder
from workflows.procurement_workflow import ProcurementWorkflow, ProcurementDecision
from api.utils import convert_numpy_types


router = APIRouter(prefix="/procurement", tags=["procurement"])


# Request/Response Models

class POApprovalRequest(BaseModel):
    approved_by: str


class PORejectionRequest(BaseModel):
    rejected_by: str
    rejection_reason: str


class POCreationRequest(BaseModel):
    sku_id: str
    supplier_id: str
    quantity: int
    reasoning: str
    created_by: str = "system"


# Endpoints

@router.post("/analyze/{sku_id}")
async def analyze_sku_for_procurement(
    sku_id: str,
    lookback_days: int = Query(default=30, ge=7, le=90),
    forecast_horizon: int = Query(default=30, ge=7, le=90),
    db: Session = Depends(get_db)
):
    """
    Analyze a single SKU for procurement needs

    Returns complete analysis:
    - Pattern analysis (trend, seasonality, volatility)
    - Demand forecast
    - Dynamic reorder point
    - Risk assessment
    - Recommended order (if needed)
    """
    try:
        workflow = ProcurementWorkflow(db)
        decision = workflow.analyze_sku(
            sku_id=sku_id,
            lookback_days=lookback_days,
            forecast_horizon=forecast_horizon
        )
        result = decision.to_dict()
        return convert_numpy_types(result)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/analyze-all")
async def analyze_all_skus_for_procurement(
    db: Session = Depends(get_db)
):
    """
    Analyze all SKUs for procurement needs

    Use case: Daily automated check
    Returns list of decisions, flagging which SKUs need reordering
    """
    try:
        workflow = ProcurementWorkflow(db)
        decisions = workflow.analyze_all_skus()

        # Convert to dict
        result = {
            "total_skus": len(decisions),
            "need_reorder": sum(1 for d in decisions if d.needs_reorder),
            "decisions": [d.to_dict() for d in decisions]
        }

        return convert_numpy_types(result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/purchase-order", status_code=201)
async def create_purchase_order(
    request: POCreationRequest,
    db: Session = Depends(get_db)
):
    """
    Create a purchase order in DRAFT status

    This creates the PO but does NOT approve it.
    Use PUT /purchase-order/{po_id}/approve to approve.
    """
    try:
        workflow = ProcurementWorkflow(db)
        po = workflow.create_purchase_order(
            sku_id=request.sku_id,
            supplier_id=request.supplier_id,
            quantity=request.quantity,
            reasoning=request.reasoning,
            created_by=request.created_by
        )
        return po.to_dict()

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PO creation failed: {str(e)}")


@router.post("/auto-generate/{sku_id}", status_code=201)
async def auto_generate_purchase_order(
    sku_id: str,
    created_by: str = Query(default="system"),
    db: Session = Depends(get_db)
):
    """
    Analyze SKU and auto-generate PO if reorder needed

    This is the "one-click" workflow:
    1. Analyze SKU
    2. If reorder needed, create PO automatically
    3. Return PO in DRAFT status for approval
    """
    try:
        workflow = ProcurementWorkflow(db)

        # Analyze
        decision = workflow.analyze_sku(sku_id)

        if not decision.needs_reorder:
            return convert_numpy_types({
                "message": "No reorder needed",
                "reasoning": decision.reasoning,
                "po_created": False
            })

        if not decision.recommended_order:
            raise HTTPException(
                status_code=500,
                detail="Reorder needed but no recommendation generated"
            )

        # Create PO
        po = workflow.create_purchase_order(
            sku_id=sku_id,
            supplier_id=decision.recommended_order['supplier_id'],
            quantity=decision.recommended_order['quantity'],
            reasoning=decision.reasoning,
            created_by=created_by
        )

        return convert_numpy_types({
            "message": "Purchase order created",
            "po_created": True,
            "purchase_order": po.to_dict(),
            "analysis": decision.to_dict()
        })

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auto-generation failed: {str(e)}")


@router.get("/purchase-order")
async def list_purchase_orders(
    status: Optional[str] = Query(default=None),
    sku_id: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db)
):
    """
    List purchase orders

    Query params:
    - status: Filter by status (draft, approved, cancelled, etc.)
    - sku_id: Filter by SKU
    - limit: Max results (default 50)
    """
    try:
        query = db.query(PurchaseOrder)

        if status:
            query = query.filter(PurchaseOrder.status == status)

        if sku_id:
            query = query.filter(PurchaseOrder.sku_id == sku_id)

        pos = query.order_by(PurchaseOrder.created_at.desc()).limit(limit).all()

        return {
            "count": len(pos),
            "purchase_orders": [po.to_dict() for po in pos]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/purchase-order/{po_id}")
async def get_purchase_order(
    po_id: str,
    db: Session = Depends(get_db)
):
    """
    Get purchase order details
    """
    po = db.query(PurchaseOrder).filter(PurchaseOrder.po_id == po_id).first()

    if not po:
        raise HTTPException(status_code=404, detail=f"Purchase order {po_id} not found")

    return po.to_dict()


@router.put("/purchase-order/{po_id}/approve")
async def approve_purchase_order(
    po_id: str,
    request: POApprovalRequest,
    db: Session = Depends(get_db)
):
    """
    Approve a purchase order

    Status transition: draft -> approved
    """
    try:
        workflow = ProcurementWorkflow(db)
        po = workflow.approve_purchase_order(
            po_id=po_id,
            approved_by=request.approved_by
        )
        return {
            "message": "Purchase order approved",
            "purchase_order": po.to_dict()
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Approval failed: {str(e)}")


@router.put("/purchase-order/{po_id}/reject")
async def reject_purchase_order(
    po_id: str,
    request: PORejectionRequest,
    db: Session = Depends(get_db)
):
    """
    Reject a purchase order

    Status transition: draft -> cancelled
    """
    try:
        workflow = ProcurementWorkflow(db)
        po = workflow.reject_purchase_order(
            po_id=po_id,
            rejected_by=request.rejected_by,
            rejection_reason=request.rejection_reason
        )
        return {
            "message": "Purchase order rejected",
            "purchase_order": po.to_dict()
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rejection failed: {str(e)}")


@router.get("/pending-approvals")
async def get_pending_approvals(
    db: Session = Depends(get_db)
):
    """
    Get all purchase orders pending approval

    Use case: Manager approval dashboard
    """
    pos = (
        db.query(PurchaseOrder)
        .filter(PurchaseOrder.status == 'draft')
        .order_by(PurchaseOrder.created_at.desc())
        .all()
    )

    return {
        "count": len(pos),
        "pending_approvals": [po.to_dict() for po in pos]
    }
