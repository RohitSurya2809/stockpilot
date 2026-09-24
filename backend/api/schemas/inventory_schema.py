"""
Pydantic schemas for Inventory API endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
from decimal import Decimal


class SKUBase(BaseModel):
    """Base SKU schema."""
    id: str = Field(..., description="SKU identifier")
    name: str = Field(..., description="Product name")
    category: Optional[str] = Field(None, description="Product category")
    unit_cost: Decimal = Field(..., description="Unit cost")
    minimum_order_quantity: Decimal = Field(..., description="Minimum order quantity")


class SKUResponse(SKUBase):
    """SKU response schema with inventory info."""
    current_stock: Optional[int] = None
    safety_stock: Optional[int] = None
    reorder_point: Optional[int] = None
    supplier_name: Optional[str] = None
    supplier_lead_time: Optional[int] = None

    class Config:
        from_attributes = True


class InventoryResponse(BaseModel):
    """Inventory response schema."""
    sku_id: str
    product_name: str
    current_stock: int
    safety_stock: int
    reorder_point: int
    last_updated: datetime

    class Config:
        from_attributes = True


class SalesHistoryResponse(BaseModel):
    """Sales history response schema."""
    sku_id: str
    date: date
    quantity_sold: int

    class Config:
        from_attributes = True


class InventorySummaryResponse(BaseModel):
    """Summary response for inventory dashboard."""
    sku_id: str
    product_name: str
    category: Optional[str]
    current_stock: int
    safety_stock: int
    reorder_point: int
    recent_daily_demand: Optional[float] = None
    demand_trend: Optional[str] = None
    risk_level: Optional[str] = None
    days_until_stockout: Optional[float] = None
    supplier_name: Optional[str] = None
    supplier_lead_time: Optional[int] = None

    class Config:
        from_attributes = True
