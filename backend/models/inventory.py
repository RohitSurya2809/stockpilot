"""
Inventory Model
"""

from sqlalchemy import Column, String, Integer, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from models.database import Base


class Inventory(Base):
    """
    Current inventory levels and reorder points for each SKU.
    """
    __tablename__ = "inventory"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Key
    sku_id = Column(String(50), ForeignKey("skus.id"), nullable=False, unique=True, index=True)

    # Inventory Levels
    current_stock = Column(Integer, nullable=False, comment="Current stock level")
    safety_stock = Column(Integer, nullable=False, comment="Safety stock buffer")
    reorder_point = Column(Integer, nullable=False, comment="Current reorder point (can be dynamic)")

    # Metadata
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="Last update time")

    # Relationships
    sku = relationship("SKU", back_populates="inventory")

    def __repr__(self):
        return f"<Inventory(sku_id='{self.sku_id}', current_stock={self.current_stock})>"

    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "sku_id": self.sku_id,
            "current_stock": self.current_stock,
            "safety_stock": self.safety_stock,
            "reorder_point": self.reorder_point,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }
