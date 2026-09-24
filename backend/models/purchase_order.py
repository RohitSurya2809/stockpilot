"""
Purchase Order Model
"""

from sqlalchemy import Column, String, Integer, Numeric, DateTime, Date, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from models.database import Base


class PurchaseOrder(Base):
    """
    Purchase order tracking model.

    Tracks procurement recommendations and approvals.
    """
    __tablename__ = "purchase_orders"

    # Primary Key
    po_id = Column(String(50), primary_key=True, index=True, comment="PO identifier (e.g., PO-20260101-0001)")

    # Foreign Keys
    sku_id = Column(String(50), ForeignKey("skus.id"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)

    # Order Details
    quantity = Column(Integer, nullable=False, comment="Order quantity")
    unit_cost = Column(Numeric(10, 2), nullable=False, comment="Unit cost at time of order")
    total_cost = Column(Numeric(12, 2), nullable=False, comment="Total order cost")
    expected_delivery_date = Column(Date, nullable=True, comment="Expected delivery date (created_at + lead_time)")

    # Status and Approval
    status = Column(
        String(50),
        nullable=False,
        default='draft',
        comment="Status: draft, pending_approval, approved, sent, received, cancelled"
    )

    # Decision Context
    reasoning = Column(Text, nullable=True, comment="AI-generated reasoning for this order")
    recommended_by = Column(String(100), nullable=True, comment="Agent ID that recommended this order")
    created_by = Column(String(100), nullable=True, comment="User/system that created this PO")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="PO creation time")

    # Approval
    approved_at = Column(DateTime(timezone=True), nullable=True, comment="Approval timestamp")
    approved_by = Column(String(100), nullable=True, comment="User who approved the order")

    # Rejection
    rejected_at = Column(DateTime(timezone=True), nullable=True, comment="Rejection timestamp")
    rejected_by = Column(String(100), nullable=True, comment="User who rejected the order")
    rejection_reason = Column(Text, nullable=True, comment="Reason for rejection")

    # Completion
    completed_at = Column(DateTime(timezone=True), nullable=True, comment="Completion timestamp")

    # Relationships
    sku = relationship("SKU", back_populates="purchase_orders")
    supplier = relationship("Supplier", back_populates="purchase_orders")

    def __repr__(self):
        return f"<PurchaseOrder(po_id='{self.po_id}', sku_id='{self.sku_id}', quantity={self.quantity}, status='{self.status}')>"

    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "po_id": self.po_id,
            "sku_id": self.sku_id,
            "supplier_id": self.supplier_id,
            "quantity": self.quantity,
            "unit_cost": float(self.unit_cost) if self.unit_cost else None,
            "total_cost": float(self.total_cost) if self.total_cost else None,
            "expected_delivery_date": self.expected_delivery_date.isoformat() if self.expected_delivery_date else None,
            "status": self.status,
            "reasoning": self.reasoning,
            "recommended_by": self.recommended_by,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "approved_by": self.approved_by,
            "rejected_at": self.rejected_at.isoformat() if self.rejected_at else None,
            "rejected_by": self.rejected_by,
            "rejection_reason": self.rejection_reason,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
