from datetime import datetime, timezone
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.catalog import ProductResponse


# =========================================================================
# Gemini Raw Structured Output Models
# =========================================================================

class GeminiProductRec(BaseModel):
    product_id: int = Field(..., description="ID of the recommended product from the candidate catalog")
    quantity: int = Field(1, ge=1, le=100, description="Recommended quantity")
    reason: str = Field(..., description="Brief reason explaining why this item fits user preferences and budget")


class GeminiInterpretedPreferences(BaseModel):
    style: Optional[str] = Field(None, description="Detected design or aesthetic style (e.g. Modern, Minimalist)")
    priority: Optional[str] = Field(None, description="Inferred user priority (e.g. budget, aesthetics, space)")
    key_aspects: List[str] = Field(default_factory=list, description="Key keywords or attributes detected")


class GeminiStructuredResponse(BaseModel):
    module: str = Field(..., description="Module name: home, party, or jewelry")
    summary: str = Field(..., description="Concise personalized planning summary")
    budget_guidance: Optional[str] = Field(None, description="Strategic financial advice for this budget")
    preferences: Optional[GeminiInterpretedPreferences] = None
    recommendations: List[GeminiProductRec] = Field(
        default_factory=list,
        description="List of recommended product IDs from catalog",
    )
    warnings: List[str] = Field(default_factory=list, description="Potential constraints or tradeoffs")


# =========================================================================
# Client API Request & Response Schemas
# =========================================================================

class RecommendationRequest(BaseModel):
    module: Literal["home", "party", "jewelry"] = Field(
        ...,
        description="Target planner domain: 'home', 'party', or 'jewelry'",
    )
    budget: float = Field(
        ...,
        gt=0,
        description="Total allocated budget limit in INR (₹)",
    )
    preferences: str = Field(
        ...,
        min_length=2,
        max_length=1500,
        description="Natural language prompt describing requirements, styles, guest count, or occasions",
    )
    save_plan: bool = Field(
        False,
        description="Whether to persist the generated plan into the database for the user",
    )
    title: Optional[str] = Field(
        None,
        max_length=200,
        description="Optional custom title for the saved plan",
    )


class RecommendedItemDetail(BaseModel):
    product: ProductResponse
    quantity: int
    subtotal: float
    reason: str

    model_config = ConfigDict(from_attributes=True)


class BudgetSummary(BaseModel):
    total_budget: float
    total_cost: float
    remaining_budget: float
    is_within_budget: bool
    over_budget_amount: float
    utilization_percentage: float
    currency: str = "INR"
    currency_symbol: str = "₹"

    model_config = ConfigDict(from_attributes=True)


class RecommendationResponse(BaseModel):
    source: Literal["gemini", "deterministic_fallback"]
    module: str
    summary: str
    budget_guidance: Optional[str] = None
    recommendations: List[RecommendedItemDetail]
    budget: BudgetSummary
    warnings: List[str] = Field(default_factory=list)
    plan_id: Optional[int] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)
