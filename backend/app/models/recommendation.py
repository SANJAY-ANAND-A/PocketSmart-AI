from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("budget_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    match_score = Column(Float, default=0.0, nullable=False)
    score_breakdown = Column(Text, nullable=True)  # JSON-encoded scoring components
    recommendation_reason = Column(Text, nullable=True)
    is_upgrade = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    plan = relationship("BudgetPlan", back_populates="recommendations")
    product = relationship("Product", back_populates="recommendations")

    def __repr__(self) -> str:
        return f"<Recommendation id={self.id} plan_id={self.plan_id} product_id={self.product_id} score={self.match_score}>"
