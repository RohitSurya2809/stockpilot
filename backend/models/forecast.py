"""
Forecast and Risk Assessment Models
"""

from sqlalchemy import Column, String, Integer, Numeric, Date, DateTime, Text, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import relationship
from models.database import Base


class Forecast(Base):
    """
    Demand forecast model.

    Stores predicted demand for future dates.
    """
    __tablename__ = "forecasts"
    __table_args__ = (
        UniqueConstraint('sku_id', 'forecast_date', name='uq_forecast_sku_date'),
    )

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Key
    sku_id = Column(String(50), ForeignKey("skus.id"), nullable=False, index=True)

    # Forecast Data
    forecast_date = Column(Date, nullable=False, index=True, comment="Date of forecasted demand")
    predicted_demand = Column(Numeric(10, 2), nullable=False, comment="Predicted demand quantity")
    confidence_level = Column(Numeric(3, 2), nullable=True, comment="Confidence level (0-1)")
    method = Column(String(100), nullable=True, comment="Forecasting method used")

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Forecast creation time")

    # Relationships
    sku = relationship("SKU", back_populates="forecasts")

    def __repr__(self):
        return f"<Forecast(sku_id='{self.sku_id}', date={self.forecast_date}, demand={self.predicted_demand})>"

    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "sku_id": self.sku_id,
            "forecast_date": self.forecast_date.isoformat() if self.forecast_date else None,
            "predicted_demand": float(self.predicted_demand) if self.predicted_demand else None,
            "confidence_level": float(self.confidence_level) if self.confidence_level else None,
            "method": self.method,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class RiskAssessment(Base):
    """
    Risk assessment model.

    Tracks stockout/overstock risk calculations.
    """
    __tablename__ = "risk_assessments"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Key
    sku_id = Column(String(50), ForeignKey("skus.id"), nullable=False, index=True)

    # Assessment Data
    assessment_date = Column(DateTime(timezone=True), server_default=func.now(), index=True, comment="Assessment timestamp")
    risk_level = Column(
        String(50),
        nullable=False,
        comment="Risk level: critical, high, medium, low"
    )
    days_until_stockout = Column(Numeric(10, 2), nullable=True, comment="Predicted days until stockout")
    stockout_probability = Column(Numeric(5, 4), nullable=True, comment="Stockout probability (0-1)")
    recommended_action = Column(Text, nullable=True, comment="Recommended action")
    dynamic_reorder_point = Column(Integer, nullable=True, comment="Calculated dynamic reorder point")

    # Relationships
    sku = relationship("SKU", back_populates="risk_assessments")

    def __repr__(self):
        return f"<RiskAssessment(sku_id='{self.sku_id}', risk_level='{self.risk_level}', days={self.days_until_stockout})>"

    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "sku_id": self.sku_id,
            "assessment_date": self.assessment_date.isoformat() if self.assessment_date else None,
            "risk_level": self.risk_level,
            "days_until_stockout": float(self.days_until_stockout) if self.days_until_stockout else None,
            "stockout_probability": float(self.stockout_probability) if self.stockout_probability else None,
            "recommended_action": self.recommended_action,
            "dynamic_reorder_point": self.dynamic_reorder_point
        }
