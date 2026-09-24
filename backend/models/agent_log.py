"""
Agent Log Model
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from models.database import Base


class AgentLog(Base):
    """
    Agent decision audit log model.

    Tracks all agent decisions for transparency and debugging.
    """
    __tablename__ = "agent_logs"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Agent Information
    agent_id = Column(String(100), nullable=False, index=True, comment="Agent identifier (e.g., InventoryAgent)")

    # Foreign Key (optional - some logs may not be SKU-specific)
    sku_id = Column(String(50), ForeignKey("skus.id"), nullable=True, index=True)

    # Decision Data
    decision_type = Column(String(100), nullable=False, index=True, comment="Type of decision made")
    reasoning = Column(Text, nullable=False, comment="Human-readable reasoning")
    decision_data = Column(JSONB, nullable=True, comment="Structured decision data (JSON)")

    # Metadata
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True, comment="Decision timestamp")

    # Relationships
    sku = relationship("SKU", back_populates="agent_logs")

    def __repr__(self):
        return f"<AgentLog(agent_id='{self.agent_id}', decision_type='{self.decision_type}', timestamp={self.timestamp})>"

    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "sku_id": self.sku_id,
            "decision_type": self.decision_type,
            "reasoning": self.reasoning,
            "decision_data": self.decision_data,  # Already JSON-serializable
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }
