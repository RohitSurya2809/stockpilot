"""
Procurement Workflow Engine

Orchestrates the end-to-end procurement decision process:
1. Analyze demand patterns
2. Forecast future demand
3. Calculate dynamic ROP
4. Assess risk
5. Generate purchase order if needed
6. Create audit trail
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from models import SKU, Inventory, SalesHistory, PurchaseOrder, Supplier, SKUSupplier
from analytics.demand_pattern_analyzer import analyze_trend, detect_seasonality, calculate_volatility
from analytics.forecaster import forecast_demand
from analytics.reorder_calculator import calculate_dynamic_reorder_point, calculate_order_quantity
from analytics.risk_engine import assess_stockout_risk


class ProcurementDecision:
    """Result of procurement analysis for one SKU"""

    def __init__(
        self,
        sku_id: str,
        needs_reorder: bool,
        reasoning: str,
        pattern_analysis: Dict[str, Any],
        forecast: Dict[str, Any],
        reorder_point: Dict[str, Any],
        risk_assessment: Dict[str, Any],
        recommended_order: Optional[Dict[str, Any]] = None
    ):
        self.sku_id = sku_id
        self.needs_reorder = needs_reorder
        self.reasoning = reasoning
        self.pattern_analysis = pattern_analysis
        self.forecast = forecast
        self.reorder_point = reorder_point
        self.risk_assessment = risk_assessment
        self.recommended_order = recommended_order
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> dict:
        return {
            "sku_id": self.sku_id,
            "needs_reorder": self.needs_reorder,
            "reasoning": self.reasoning,
            "pattern_analysis": self.pattern_analysis,
            "forecast": self.forecast,
            "reorder_point": self.reorder_point,
            "risk_assessment": self.risk_assessment,
            "recommended_order": self.recommended_order,
            "timestamp": self.timestamp.isoformat()
        }


class ProcurementWorkflow:
    """
    End-to-end procurement workflow orchestrator

    This is the intelligence layer that connects all analytics
    and makes procurement decisions.
    """

    def __init__(self, db: Session):
        self.db = db

    def analyze_sku(
        self,
        sku_id: str,
        lookback_days: int = 30,
        forecast_horizon: int = 30
    ) -> ProcurementDecision:
        """
        Complete analysis for one SKU

        Steps:
        1. Get current inventory and sales history
        2. Analyze demand patterns (trend, seasonality, volatility)
        3. Generate demand forecast
        4. Calculate dynamic reorder point
        5. Assess stockout risk
        6. Decide if reorder needed
        7. Calculate order quantity if needed
        """
        # Step 1: Get data
        sku = self.db.query(SKU).filter(SKU.id == sku_id).first()
        if not sku:
            raise ValueError(f"SKU {sku_id} not found")

        inventory = self.db.query(Inventory).filter(Inventory.sku_id == sku_id).first()
        if not inventory:
            raise ValueError(f"Inventory record for {sku_id} not found")

        # Get sales history
        cutoff_date = datetime.utcnow().date() - timedelta(days=lookback_days)
        sales_records = (
            self.db.query(SalesHistory)
            .filter(
                SalesHistory.sku_id == sku_id,
                SalesHistory.date >= cutoff_date
            )
            .order_by(SalesHistory.date.asc())
            .all()
        )

        if len(sales_records) < 7:
            # Not enough data
            return ProcurementDecision(
                sku_id=sku_id,
                needs_reorder=False,
                reasoning="Insufficient sales history (< 7 days)",
                pattern_analysis={},
                forecast={},
                reorder_point={},
                risk_assessment={}
            )

        daily_demand = [record.quantity_sold for record in sales_records]

        # Step 2: Analyze pattern
        trend = analyze_trend(daily_demand, window_days=min(len(daily_demand), 30))
        seasonality = detect_seasonality(daily_demand)
        volatility = calculate_volatility(daily_demand)

        pattern_analysis = {
            "trend": trend,
            "seasonality": seasonality,
            "volatility": volatility
        }

        # Step 3: Forecast
        forecast_result = forecast_demand(
            daily_demand,
            forecast_horizon_days=forecast_horizon,
            moving_avg_window=min(14, len(daily_demand))
        )

        # Step 4: Get supplier lead time
        primary_supplier = (
            self.db.query(SKUSupplier)
            .filter(
                SKUSupplier.sku_id == sku_id,
                SKUSupplier.is_primary == True
            )
            .first()
        )

        if not primary_supplier:
            # Fallback: use any supplier
            primary_supplier = (
                self.db.query(SKUSupplier)
                .filter(SKUSupplier.sku_id == sku_id)
                .first()
            )

        if not primary_supplier:
            raise ValueError(f"No supplier found for SKU {sku_id}")

        lead_time_days = primary_supplier.supplier.lead_time_days

        # Calculate dynamic ROP
        rop_result = calculate_dynamic_reorder_point(
            sales_data=daily_demand,
            supplier_lead_time_days=lead_time_days,
            service_level=0.95
        )

        # Extract stats for later use
        avg_demand = volatility['mean_demand']

        # Step 5: Assess risk
        risk_result = assess_stockout_risk(
            current_inventory=inventory.current_stock,
            sales_data=daily_demand,
            supplier_lead_time_days=lead_time_days,
            dynamic_reorder_point=rop_result['dynamic_reorder_point']
        )

        # Step 6: Decide if reorder needed
        needs_reorder = inventory.current_stock < rop_result['dynamic_reorder_point']

        # Generate reasoning
        reasoning = self._generate_reasoning(
            sku=sku,
            inventory=inventory,
            pattern_analysis=pattern_analysis,
            rop_result=rop_result,
            risk_result=risk_result,
            needs_reorder=needs_reorder,
            lead_time_days=lead_time_days
        )

        # Step 7: Calculate order quantity if needed
        recommended_order = None
        if needs_reorder:
            order_qty = calculate_order_quantity(
                current_inventory=inventory.current_stock,
                reorder_point=rop_result['dynamic_reorder_point'],
                lead_time_days=lead_time_days,
                avg_daily_demand=avg_demand,
                forecast=forecast_result['forecast']
            )

            recommended_order = {
                "supplier_id": primary_supplier.supplier_id,
                "quantity": order_qty['recommended_quantity'],
                "unit_cost": primary_supplier.cost_per_unit,
                "total_cost": order_qty['recommended_quantity'] * primary_supplier.cost_per_unit,
                "lead_time_days": lead_time_days,
                "rationale": order_qty['rationale']
            }

        return ProcurementDecision(
            sku_id=sku_id,
            needs_reorder=needs_reorder,
            reasoning=reasoning,
            pattern_analysis=pattern_analysis,
            forecast=forecast_result,
            reorder_point=rop_result,
            risk_assessment=risk_result,
            recommended_order=recommended_order
        )

    def analyze_all_skus(self) -> List[ProcurementDecision]:
        """
        Analyze all SKUs and return decisions

        Use case: Daily automated check
        """
        skus = self.db.query(SKU).all()
        decisions = []

        for sku in skus:
            try:
                decision = self.analyze_sku(sku.id)
                decisions.append(decision)
            except Exception as e:
                print(f"Error analyzing SKU {sku.id}: {str(e)}")
                continue

        return decisions

    def create_purchase_order(
        self,
        sku_id: str,
        supplier_id: str,
        quantity: int,
        reasoning: str,
        created_by: str = "system"
    ) -> PurchaseOrder:
        """
        Create a purchase order in DRAFT status

        This creates the PO but does NOT approve it.
        Human approval required via approve_purchase_order()
        """
        sku = self.db.query(SKU).filter(SKU.id == sku_id).first()
        if not sku:
            raise ValueError(f"SKU {sku_id} not found")

        supplier = self.db.query(Supplier).filter(Supplier.supplier_id == supplier_id).first()
        if not supplier:
            raise ValueError(f"Supplier {supplier_id} not found")

        sku_supplier = (
            self.db.query(SKUSupplier)
            .filter(
                SKUSupplier.sku_id == sku_id,
                SKUSupplier.supplier_id == supplier_id
            )
            .first()
        )

        if not sku_supplier:
            raise ValueError(f"SKU {sku_id} not available from supplier {supplier_id}")

        # Generate PO ID
        po_count = self.db.query(PurchaseOrder).count()
        po_id = f"PO-{datetime.utcnow().strftime('%Y%m%d')}-{po_count + 1:04d}"

        # Calculate expected delivery
        expected_delivery = datetime.utcnow().date() + timedelta(days=sku_supplier.supplier.lead_time_days)

        # Create PO
        po = PurchaseOrder(
            po_id=po_id,
            sku_id=sku_id,
            supplier_id=supplier_id,
            quantity=quantity,
            unit_cost=sku_supplier.cost_per_unit,
            total_cost=quantity * sku_supplier.cost_per_unit,
            status="draft",
            expected_delivery_date=expected_delivery,
            reasoning=reasoning,
            created_by=created_by
        )

        self.db.add(po)
        self.db.commit()
        self.db.refresh(po)

        return po

    def approve_purchase_order(
        self,
        po_id: str,
        approved_by: str
    ) -> PurchaseOrder:
        """
        Approve a purchase order

        Status transition: draft -> pending_approval -> approved
        """
        po = self.db.query(PurchaseOrder).filter(PurchaseOrder.po_id == po_id).first()
        if not po:
            raise ValueError(f"Purchase order {po_id} not found")

        if po.status == "approved":
            raise ValueError(f"Purchase order {po_id} already approved")

        if po.status == "cancelled":
            raise ValueError(f"Purchase order {po_id} is cancelled")

        po.status = "approved"
        po.approved_by = approved_by
        po.approved_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(po)

        return po

    def reject_purchase_order(
        self,
        po_id: str,
        rejected_by: str,
        rejection_reason: str
    ) -> PurchaseOrder:
        """
        Reject a purchase order

        Status transition: draft/pending_approval -> cancelled
        """
        po = self.db.query(PurchaseOrder).filter(PurchaseOrder.po_id == po_id).first()
        if not po:
            raise ValueError(f"Purchase order {po_id} not found")

        if po.status in ["approved", "sent", "received"]:
            raise ValueError(f"Cannot reject purchase order {po_id} - already {po.status}")

        po.status = "cancelled"
        po.rejection_reason = rejection_reason
        po.rejected_by = rejected_by
        po.rejected_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(po)

        return po

    def _generate_reasoning(
        self,
        sku,
        inventory,
        pattern_analysis,
        rop_result,
        risk_result,
        needs_reorder,
        lead_time_days
    ) -> str:
        """
        Generate human-readable reasoning for the decision
        """
        trend_info = pattern_analysis['trend']
        risk_info = risk_result

        reasoning_parts = [
            f"SKU: {sku.name} ({sku.id})",
            f"Current Stock: {inventory.current_stock} units",
            f"Dynamic ROP: {rop_result['dynamic_reorder_point']} units",
        ]

        # Trend
        if trend_info['trend'] == 'increasing':
            reasoning_parts.append(f"Demand trend: INCREASING ({trend_info['trend_percentage']:.1f}%)")
        elif trend_info['trend'] == 'decreasing':
            reasoning_parts.append(f"Demand trend: DECREASING ({trend_info['trend_percentage']:.1f}%)")
        else:
            reasoning_parts.append("Demand trend: STABLE")

        # Risk
        reasoning_parts.append(f"Risk Level: {risk_info['risk_level'].upper()}")
        reasoning_parts.append(f"Days until stockout: {risk_info['days_until_stockout']:.1f}")
        reasoning_parts.append(f"Supplier lead time: {lead_time_days} days")

        # Decision
        if needs_reorder:
            if risk_info['risk_level'] == 'critical':
                reasoning_parts.append("DECISION: IMMEDIATE REORDER REQUIRED - Stockout will occur before supplier can deliver")
            elif risk_info['risk_level'] == 'high':
                reasoning_parts.append("DECISION: URGENT REORDER REQUIRED - Little buffer before stockout")
            else:
                reasoning_parts.append("DECISION: REORDER RECOMMENDED - Below reorder point")
        else:
            reasoning_parts.append("DECISION: NO REORDER NEEDED - Stock sufficient")

        return " | ".join(reasoning_parts)


# Test function
if __name__ == "__main__":
    from models.database import SessionLocal

    print("=" * 70)
    print("PROCUREMENT WORKFLOW - TEST")
    print("=" * 70)
    print()

    db = SessionLocal()

    try:
        workflow = ProcurementWorkflow(db)

        print("Test 1: Analyze Demo SKU (SKU-004)")
        print("-" * 70)

        decision = workflow.analyze_sku("SKU-004")

        print(f"SKU: {decision.sku_id}")
        print(f"Needs Reorder: {decision.needs_reorder}")
        print(f"\nReasoning:")
        print(decision.reasoning)
        print()

        if decision.needs_reorder and decision.recommended_order:
            print("Recommended Order:")
            print(f"  Supplier: {decision.recommended_order['supplier_id']}")
            print(f"  Quantity: {decision.recommended_order['quantity']} units")
            print(f"  Total Cost: ${decision.recommended_order['total_cost']:.2f}")
            print(f"  Lead Time: {decision.recommended_order['lead_time_days']} days")
            print()

        print("\nTest 2: Create Purchase Order")
        print("-" * 70)

        if decision.needs_reorder and decision.recommended_order:
            po = workflow.create_purchase_order(
                sku_id=decision.sku_id,
                supplier_id=decision.recommended_order['supplier_id'],
                quantity=decision.recommended_order['quantity'],
                reasoning=decision.reasoning,
                created_by="test_user"
            )

            print(f"Created: {po.po_id}")
            print(f"Status: {po.status}")
            print(f"Quantity: {po.quantity} units")
            print(f"Total Cost: ${po.total_cost:.2f}")
            print(f"Expected Delivery: {po.expected_delivery_date}")
            print()

            print("\nTest 3: Approve Purchase Order")
            print("-" * 70)

            po = workflow.approve_purchase_order(po.po_id, approved_by="manager")

            print(f"PO {po.po_id} status: {po.status}")
            print(f"Approved by: {po.approved_by}")
            print(f"Approved at: {po.approved_at}")
        else:
            print("SKU-004 does not need reorder (sufficient stock)")

        print()
        print("=" * 70)
        print("SUCCESS: Procurement workflow working")
        print("=" * 70)

    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()
