"""
Purchase Order Model
"""

from sqlalchemy import Column, String, Integer, Numeric, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from models.database import Base


class PurchaseOrder(Base):
    """
    Purchase order tracking model.

    Tracks procurement recommendations and approvals.
    """
    __tablename__ = "purchase_orders"

    # Primary Key
    id = Column(String(50), primary_key=True, index=True, comment="PO identifier (e.g., PO-1042)")

    # Foreign Keys
    sku_id = Column(String(50), ForeignKey("skus.id"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)

    # Order Details
    quantity = Column(Integer, nullable=False, comment="Order quantity")
    unit_cost = Column(Numeric(10, 2), nullable=False, comment="Unit cost at time of order")
    total_cost = Column(Numeric(12, 2), nullable=False, comment="Total order cost")

    # Status and Approval
    status = Column(
        String(50),
        nullable=False,
        default='pending',
        comment="Status: pending, approved, rejected, completed"
    )

    # Decision Context
    reasoning = Column(Text, nullable=True, comment="AI-generated reasoning for this order")
    recommended_by = Column(String(100), nullable=True, comment="Agent ID that recommended this order")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="PO creation time")
    approved_at = Column(DateTime(timezone=True), nullable=True, comment="Approval timestamp")
    approved_by = Column(String(100), nullable=True, comment="User who approved the order")
    completed_at = Column(DateTime(timezone=True), nullable=True, comment="Completion timestamp")

    # Relationships
    sku = relationship("SKU", back_populates="purchase_orders")
    supplier = relationship("Supplier", back_populates="purchase_orders")

    def __repr__(self):
        return f"<PurchaseOrder(id='{self.id}', sku_id='{self.sku_id}', quantity={self.quantity}, status='{self.status}')>"

    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "sku_id": self.sku_id,
            "supplier_id": self.supplier_id,
            "quantity": self.quantity,
            "unit_cost": float(self.unit_cost) if self.unit_cost else None,
            "total_cost": float(self.total_cost) if self.total_cost else None,
            "status": self.status,
            "reasoning": self.reasoning,
            "recommended_by": self.recommended_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "approved_by": self.approved_by,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
