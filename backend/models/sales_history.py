"""
Sales History Model
"""

from sqlalchemy import Column, String, Integer, Date, DateTime, func, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from models.database import Base


class SalesHistory(Base):
    """
    Historical sales/usage data for demand analysis.
    """
    __tablename__ = "sales_history"
    __table_args__ = (
        UniqueConstraint('sku_id', 'date', name='uq_sales_sku_date'),
    )

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Key
    sku_id = Column(String(50), ForeignKey("skus.id"), nullable=False, index=True)

    # Sales Data
    date = Column(Date, nullable=False, index=True, comment="Date of sales record")
    quantity_sold = Column(Integer, nullable=False, comment="Quantity sold/used on this date")

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Record creation time")

    # Relationships
    sku = relationship("SKU", back_populates="sales_history")

    def __repr__(self):
        return f"<SalesHistory(sku_id='{self.sku_id}', date={self.date}, quantity={self.quantity_sold})>"

    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "sku_id": self.sku_id,
            "date": self.date.isoformat() if self.date else None,
            "quantity_sold": self.quantity_sold,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
