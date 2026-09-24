"""
Supplier Models
"""

from sqlalchemy import Column, String, Integer, Numeric, DateTime, Boolean, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import relationship
from models.database import Base


class Supplier(Base):
    """
    Supplier information model.
    """
    __tablename__ = "suppliers"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Supplier Information
    name = Column(String(200), nullable=False, comment="Supplier name")
    contact_email = Column(String(200), nullable=True, comment="Contact email")
    lead_time_days = Column(Integer, nullable=False, comment="Delivery lead time in days")
    reliability_score = Column(Numeric(3, 2), default=1.0, comment="Reliability score (0-1)")

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Record creation time")

    # Relationships
    sku_suppliers = relationship("SKUSupplier", back_populates="supplier")
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")

    def __repr__(self):
        return f"<Supplier(id={self.id}, name='{self.name}', lead_time={self.lead_time_days})>"

    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "contact_email": self.contact_email,
            "lead_time_days": self.lead_time_days,
            "reliability_score": float(self.reliability_score) if self.reliability_score else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class SKUSupplier(Base):
    """
    Junction table for SKU-Supplier many-to-many relationship.

    Stores supplier-specific pricing and preferences for each SKU.
    """
    __tablename__ = "sku_suppliers"
    __table_args__ = (
        UniqueConstraint('sku_id', 'supplier_id', name='uq_sku_supplier'),
    )

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    sku_id = Column(String(50), ForeignKey("skus.id"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)

    # Supplier-Specific Pricing
    cost_per_unit = Column(Numeric(10, 2), nullable=False, comment="Cost per unit from this supplier")
    is_primary = Column(Boolean, default=False, comment="Is this the primary supplier for this SKU?")

    # Relationships
    sku = relationship("SKU", back_populates="sku_suppliers")
    supplier = relationship("Supplier", back_populates="sku_suppliers")

    def __repr__(self):
        return f"<SKUSupplier(sku_id='{self.sku_id}', supplier_id={self.supplier_id}, cost={self.cost_per_unit})>"

    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "sku_id": self.sku_id,
            "supplier_id": self.supplier_id,
            "cost_per_unit": float(self.cost_per_unit) if self.cost_per_unit else None,
            "is_primary": self.is_primary
        }
