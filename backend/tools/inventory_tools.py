"""
Inventory Tools

Concrete tools for inventory operations
"""

from typing import Optional, Type, List, Dict, Any
from pydantic import Field
from datetime import datetime, timedelta

from tools.base import Tool, ToolInput, ToolOutput, tool_registry
from models.database import SessionLocal
from models import SKU, Inventory, SalesHistory, Supplier, SKUSupplier


# ========================================
# Input/Output Schemas
# ========================================

class GetInventoryInput(ToolInput):
    """Input for GetInventoryTool"""
    sku_id: str = Field(description="SKU identifier")


class GetInventoryOutput(ToolOutput):
    """Output for GetInventoryTool"""
    sku_id: Optional[str] = None
    product_name: Optional[str] = None
    current_stock: Optional[int] = None
    safety_stock: Optional[int] = None
    reorder_point: Optional[int] = None


class GetSalesHistoryInput(ToolInput):
    """Input for GetSalesHistoryTool"""
    sku_id: str = Field(description="SKU identifier")
    days: int = Field(default=30, description="Number of days to look back")


class GetSalesHistoryOutput(ToolOutput):
    """Output for GetSalesHistoryTool"""
    sku_id: Optional[str] = None
    sales_data: Optional[List[Dict[str, Any]]] = None
    daily_demand: Optional[List[float]] = None
    total_records: Optional[int] = None


class GetSupplierInput(ToolInput):
    """Input for GetSupplierTool"""
    sku_id: str = Field(description="SKU identifier")
    primary_only: bool = Field(default=True, description="Get only primary supplier")


class GetSupplierOutput(ToolOutput):
    """Output for GetSupplierTool"""
    supplier_id: Optional[int] = None
    supplier_name: Optional[str] = None
    lead_time_days: Optional[int] = None
    cost_per_unit: Optional[float] = None
    is_primary: Optional[bool] = None


# ========================================
# Tools
# ========================================

class GetInventoryTool(Tool):
    """
    Fetches current inventory data for a SKU

    Returns:
    - Current stock level
    - Safety stock
    - Reorder point
    - Product information
    """

    @property
    def input_schema(self) -> Type[ToolInput]:
        return GetInventoryInput

    @property
    def output_schema(self) -> Type[ToolOutput]:
        return GetInventoryOutput

    def _execute(self, input_data: GetInventoryInput) -> GetInventoryOutput:
        db = SessionLocal()
        try:
            sku = db.query(SKU).filter(SKU.id == input_data.sku_id).first()
            if not sku:
                return GetInventoryOutput(
                    success=False,
                    error=f"SKU {input_data.sku_id} not found"
                )

            inventory = db.query(Inventory).filter(Inventory.sku_id == input_data.sku_id).first()
            if not inventory:
                return GetInventoryOutput(
                    success=False,
                    error=f"Inventory record for {input_data.sku_id} not found"
                )

            return GetInventoryOutput(
                success=True,
                data={
                    "sku_id": sku.id,
                    "product_name": sku.name,
                    "current_stock": inventory.current_stock,
                    "safety_stock": inventory.safety_stock,
                    "reorder_point": inventory.reorder_point
                },
                sku_id=sku.id,
                product_name=sku.name,
                current_stock=inventory.current_stock,
                safety_stock=inventory.safety_stock,
                reorder_point=inventory.reorder_point
            )

        finally:
            db.close()


class GetSalesHistoryTool(Tool):
    """
    Fetches historical sales data for a SKU

    Returns:
    - Sales records for specified period
    - Daily demand values
    - Total record count
    """

    @property
    def input_schema(self) -> Type[ToolInput]:
        return GetSalesHistoryInput

    @property
    def output_schema(self) -> Type[ToolOutput]:
        return GetSalesHistoryOutput

    def _execute(self, input_data: GetSalesHistoryInput) -> GetSalesHistoryOutput:
        db = SessionLocal()
        try:
            cutoff_date = datetime.utcnow().date() - timedelta(days=input_data.days)

            sales_records = (
                db.query(SalesHistory)
                .filter(
                    SalesHistory.sku_id == input_data.sku_id,
                    SalesHistory.date >= cutoff_date
                )
                .order_by(SalesHistory.date.asc())
                .all()
            )

            if not sales_records:
                return GetSalesHistoryOutput(
                    success=False,
                    error=f"No sales history found for {input_data.sku_id}"
                )

            sales_data = [
                {
                    "date": record.date.isoformat(),
                    "quantity_sold": record.quantity_sold
                }
                for record in sales_records
            ]

            daily_demand = [record.quantity_sold for record in sales_records]

            return GetSalesHistoryOutput(
                success=True,
                data={
                    "sales_data": sales_data,
                    "daily_demand": daily_demand,
                    "total_records": len(sales_records)
                },
                sku_id=input_data.sku_id,
                sales_data=sales_data,
                daily_demand=daily_demand,
                total_records=len(sales_records)
            )

        finally:
            db.close()


class GetSupplierTool(Tool):
    """
    Fetches supplier information for a SKU

    Returns:
    - Supplier details
    - Lead time
    - Cost per unit
    """

    @property
    def input_schema(self) -> Type[ToolInput]:
        return GetSupplierInput

    @property
    def output_schema(self) -> Type[ToolOutput]:
        return GetSupplierOutput

    def _execute(self, input_data: GetSupplierInput) -> GetSupplierOutput:
        db = SessionLocal()
        try:
            query = db.query(SKUSupplier).filter(SKUSupplier.sku_id == input_data.sku_id)

            if input_data.primary_only:
                sku_supplier = query.filter(SKUSupplier.is_primary == True).first()
            else:
                sku_supplier = query.first()

            if not sku_supplier:
                return GetSupplierOutput(
                    success=False,
                    error=f"No supplier found for {input_data.sku_id}"
                )

            supplier = sku_supplier.supplier

            return GetSupplierOutput(
                success=True,
                data={
                    "supplier_id": supplier.id,
                    "supplier_name": supplier.name,
                    "lead_time_days": supplier.lead_time_days,
                    "cost_per_unit": float(sku_supplier.cost_per_unit),
                    "is_primary": sku_supplier.is_primary
                },
                supplier_id=supplier.id,
                supplier_name=supplier.name,
                lead_time_days=supplier.lead_time_days,
                cost_per_unit=float(sku_supplier.cost_per_unit),
                is_primary=sku_supplier.is_primary
            )

        finally:
            db.close()


# Register tools
tool_registry.register(GetInventoryTool)
tool_registry.register(GetSalesHistoryTool)
tool_registry.register(GetSupplierTool)
