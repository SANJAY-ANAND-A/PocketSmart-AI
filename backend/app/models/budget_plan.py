from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class BudgetPlan(Base):
    __tablename__ = "budget_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    # module_type: 'home', 'party', 'jewelry'
    module_type = Column(String(50), nullable=False, index=True)
    total_budget = Column(Float, nullable=False)
    allocated_budget = Column(Float, nullable=False)
    remaining_budget = Column(Float, nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    preferences = Column(Text, nullable=True)  # JSON-encoded user input configuration
    ai_reasoning = Column(Text, nullable=True)  # AI-generated strategic rationale
    is_fallback = Column(Boolean, default=False, nullable=False)  # True if generated via rule-based fallback
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="budget_plans")
    items = relationship("BudgetItem", back_populates="plan", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="plan", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<BudgetPlan id={self.id} module='{self.module_type}' total={self.total_budget} allocated={self.allocated_budget}>"


class BudgetItem(Base):
    __tablename__ = "budget_items"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("budget_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    category_name = Column(String(100), nullable=False)
    allocated_amount = Column(Float, nullable=False)
    spent_amount = Column(Float, default=0.0, nullable=False)
    priority = Column(String(20), default="medium", nullable=False)  # 'high', 'medium', 'low'
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    plan = relationship("BudgetPlan", back_populates="items")

    def __repr__(self) -> str:
        return f"<BudgetItem id={self.id} category='{self.category_name}' allocated={self.allocated_amount}>"
