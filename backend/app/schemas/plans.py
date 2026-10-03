from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.catalog import ProductResponse


class SavedPlanListItem(BaseModel):
    id: int
    title: str
    module_type: str
    total_budget: float
    allocated_budget: float
    remaining_budget: float
    currency: str = "INR"
    currency_symbol: str = "₹"
    is_fallback: bool = False
    items_count: int = 0
    recommendations_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SavedPlanListResponse(BaseModel):
    items: List[SavedPlanListItem]
    total: int

    model_config = ConfigDict(from_attributes=True)


class SavedPlanBudgetItem(BaseModel):
    id: int
    category_name: str
    allocated_amount: float
    spent_amount: float
    priority: str = "medium"
    reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SavedPlanRecommendation(BaseModel):
    id: int
    product_id: int
    match_score: float
    recommendation_reason: Optional[str] = None
    is_upgrade: bool = False
    product: Optional[ProductResponse] = None

    model_config = ConfigDict(from_attributes=True)


class SavedPlanDetailResponse(BaseModel):
    id: int
    title: str
    module_type: str
    total_budget: float
    allocated_budget: float
    remaining_budget: float
    currency: str = "INR"
    currency_symbol: str = "₹"
    is_fallback: bool = False
    preferences: Optional[Dict[str, Any]] = None
    ai_reasoning: Optional[str] = None
    items: List[SavedPlanBudgetItem] = Field(default_factory=list)
    recommendations: List[SavedPlanRecommendation] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeletePlanResponse(BaseModel):
    detail: str
    plan_id: int
