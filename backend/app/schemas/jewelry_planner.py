from datetime import datetime, timezone
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.recommendation import BudgetSummary, RecommendedItemDetail

ALLOWED_OCCASIONS = [
    "wedding",
    "engagement",
    "birthday",
    "party",
    "traditional_event",
    "formal_event",
]

ALLOWED_JEWELRY_TYPES = [
    "necklace",
    "earrings",
    "bracelet",
    "ring",
    "pendant",
    "bangles",
    "complete_set",
    "any",
]

ALLOWED_METALS = [
    "gold",
    "rose_gold",
    "silver",
    "platinum",
    "brass",
    "oxidized_silver",
    "any",
]


class JewelryPlanRequest(BaseModel):
    budget: float = Field(
        ...,
        gt=0,
        description="Total allocated budget limit in INR (₹), must be positive.",
    )
    occasion: str = Field(
        ...,
        description=f"Occasion or event type. Allowed values: {', '.join(ALLOWED_OCCASIONS)}",
    )
    style: Optional[str] = Field(
        "Traditional",
        description="Preferred aesthetic style (e.g. Traditional, Minimalist, Modern, Bohemian, Antique)",
    )
    preferred_metal: Optional[str] = Field(
        "gold",
        description=f"Preferred metal finish. Allowed values: {', '.join(ALLOWED_METALS)}",
    )
    preferred_color: Optional[str] = Field(
        None,
        description="Preferred stone or accent color (e.g. green, ruby-red, emerald, pearl-white, diamond)",
    )
    jewelry_type: Optional[str] = Field(
        "any",
        description=f"Primary target jewelry type or set. Allowed values: {', '.join(ALLOWED_JEWELRY_TYPES)}",
    )
    preferences: Optional[str] = Field(
        None,
        max_length=1500,
        description="Optional natural-language description, outfit notes, or specific requirements",
    )
    title: Optional[str] = Field(
        None,
        max_length=200,
        description="Optional custom title for the saved jewelry plan",
    )

    @field_validator("occasion")
    @classmethod
    def validate_occasion(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Occasion cannot be empty.")
        normalized = v.strip().lower().replace(" ", "_").replace("-", "_")
        if normalized not in ALLOWED_OCCASIONS:
            raise ValueError(
                f"Invalid occasion '{v}'. Allowed values are: {', '.join(ALLOWED_OCCASIONS)}"
            )
        return normalized

    @field_validator("jewelry_type")
    @classmethod
    def validate_jewelry_type(cls, v: Optional[str]) -> str:
        if not v or not v.strip():
            return "any"
        normalized = v.strip().lower().replace(" ", "_").replace("-", "_")
        if normalized not in ALLOWED_JEWELRY_TYPES:
            raise ValueError(
                f"Invalid jewelry_type '{v}'. Allowed values are: {', '.join(ALLOWED_JEWELRY_TYPES)}"
            )
        return normalized

    @field_validator("preferred_metal")
    @classmethod
    def validate_metal(cls, v: Optional[str]) -> str:
        if not v or not v.strip():
            return "any"
        normalized = v.strip().lower().replace(" ", "_").replace("-", "_")
        if normalized not in ALLOWED_METALS:
            return "any"
        return normalized


class JewelryCategoryAllocation(BaseModel):
    category: str
    allocated_amount: float
    percentage: float

    model_config = ConfigDict(from_attributes=True)


class JewelryPlanDetails(BaseModel):
    occasion: str
    style: Optional[str] = None
    preferred_metal: Optional[str] = None
    preferred_color: Optional[str] = None
    jewelry_type: Optional[str] = None
    outfit_analyzed: bool = False

    model_config = ConfigDict(from_attributes=True)


class JewelryPlanResponse(BaseModel):
    module: str = "jewelry"
    source: Literal["gemini", "deterministic_fallback"]
    plan_id: Optional[int] = None
    plan: JewelryPlanDetails
    category_allocations: List[JewelryCategoryAllocation] = Field(default_factory=list)
    summary: str
    budget_guidance: Optional[str] = None
    recommendations: List[RecommendedItemDetail]
    budget: BudgetSummary
    warnings: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)
