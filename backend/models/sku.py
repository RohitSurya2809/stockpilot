"""
SKU (Stock Keeping Unit) Model
"""

from sqlalchemy import Column, String, Numeric, DateTime, func
from sqlalchemy.orm import relationship
from models.database import Base


class SKU(Base):
    """
    Product/SKU information model.

    Represents individual products in the inventory system.
    """
    __tablename__ = "skus"

    # Primary Key
    id = Column(String(50), primary_key=True, index=True, comment="SKU identifier (e.g., WM-104)")

    # Basic Information
    name = Column(String(200), nullable=False, comment="Product name")
    category = Column(String(100), nullable=True, comment="Product category")
    unit_cost = Column(Numeric(10, 2), nullable=False, comment="Base unit cost")
    minimum_order_quantity = Column(Numeric(10, 2), default=1, comment="Minimum order quantity")

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Record creation time")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="Record last update time")

    # Relationships
    inventory = relationship("Inventory", back_populates="sku", uselist=False)
    sales_history = relationship("SalesHistory", back_populates="sku", order_by="SalesHistory.date")
    sku_suppliers = relationship("SKUSupplier", back_populates="sku")
    purchase_orders = relationship("PurchaseOrder", back_populates="sku")
    forecasts = relationship("Forecast", back_populates="sku", order_by="Forecast.forecast_date")
    risk_assessments = relationship("RiskAssessment", back_populates="sku", order_by="RiskAssessment.assessment_date.desc()")
    agent_logs = relationship("AgentLog", back_populates="sku")

    def __repr__(self):
        return f"<SKU(id='{self.id}', name='{self.name}')>"

    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "unit_cost": float(self.unit_cost) if self.unit_cost else None,
            "minimum_order_quantity": float(self.minimum_order_quantity) if self.minimum_order_quantity else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
