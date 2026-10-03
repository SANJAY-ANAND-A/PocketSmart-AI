import json
from datetime import datetime, timezone
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.recommendation import BudgetSummary, RecommendedItemDetail

ALLOWED_ROOM_TYPES = [
    "bedroom",
    "living_room",
    "dining_room",
    "home_office",
    "kitchen",
    "studio",
    "balcony",
]


class HomePlanRequest(BaseModel):
    budget: float = Field(
        ...,
        gt=0,
        description="Total allocated budget limit in INR (₹), must be positive.",
    )
    room_type: str = Field(
        ...,
        description=f"Room or space type. Allowed values: {', '.join(ALLOWED_ROOM_TYPES)}",
    )
    style: Optional[str] = Field(
        "Modern Minimalist",
        description="Preferred aesthetic style (e.g. Modern, Minimalist, Scandinavian, Bohemian, Industrial, Traditional)",
    )
    color_preferences: List[str] = Field(
        default_factory=list,
        description="List of color preferences (e.g. ['white', 'beige', 'wood'])",
    )
    priorities: List[str] = Field(
        default_factory=list,
        description="High-priority furniture categories (e.g. ['bed', 'wardrobe'])",
    )
    required_items: List[str] = Field(
        default_factory=list,
        description="Specific must-have items (e.g. ['queen bed', 'study desk'])",
    )
    preferences: Optional[str] = Field(
        None,
        max_length=1500,
        description="Optional natural-language requirements, room dimensions, or lifestyle requirements",
    )
    title: Optional[str] = Field(
        None,
        max_length=200,
        description="Optional custom title for the saved home plan",
    )

    @field_validator("room_type")
    @classmethod
    def validate_room_type(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Room type cannot be empty.")
        normalized = v.strip().lower().replace(" ", "_").replace("-", "_")
        if normalized not in ALLOWED_ROOM_TYPES:
            raise ValueError(
                f"Invalid room_type '{v}'. Allowed types are: {', '.join(ALLOWED_ROOM_TYPES)}"
            )
        return normalized


class HomePlanDetails(BaseModel):
    room_type: str
    style: Optional[str] = None
    colors: List[str] = Field(default_factory=list)
    priorities: List[str] = Field(default_factory=list)
    required_items: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class HomePlanResponse(BaseModel):
    module: str = "home"
    source: Literal["gemini", "deterministic_fallback"]
    plan: HomePlanDetails
    summary: str
    budget_guidance: Optional[str] = None
    recommendations: List[RecommendedItemDetail]
    budget: BudgetSummary
    warnings: List[str] = Field(default_factory=list)
    plan_id: Optional[int] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)
