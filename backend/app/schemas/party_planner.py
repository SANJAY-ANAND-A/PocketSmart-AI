from datetime import datetime, timezone
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.recommendation import BudgetSummary, RecommendedItemDetail

ALLOWED_EVENT_TYPES = [
    "birthday",
    "wedding",
    "corporate_event",
    "college_event",
    "anniversary",
    "small_gathering",
]

ALLOWED_VENUE_TYPES = [
    "banquet_hall",
    "hotel",
    "outdoor",
    "restaurant",
    "community_hall",
    "home",
    "college_campus",
    "other",
]


class PartyPlanRequest(BaseModel):
    budget: float = Field(
        ...,
        gt=0,
        description="Total allocated budget limit in INR (₹), must be positive.",
    )
    guest_count: int = Field(
        ...,
        gt=0,
        le=10000,
        description="Expected number of attendees/guests (1 to 10,000).",
    )
    event_type: str = Field(
        ...,
        description=f"Type of event. Allowed values: {', '.join(ALLOWED_EVENT_TYPES)}",
    )
    venue_type: str = Field(
        ...,
        description=f"Preferred venue type. Allowed values: {', '.join(ALLOWED_VENUE_TYPES)}",
    )
    food_preference: Optional[str] = Field(
        "multicuisine",
        description="Food style or preference (e.g. vegetarian, non-vegetarian, jain, vegan, multicuisine, street_food)",
    )
    decoration_preference: Optional[str] = Field(
        "elegant",
        description="Decoration theme/style (e.g. elegant, floral, balloon, minimal, bohemian, grand)",
    )
    entertainment_preference: Optional[str] = Field(
        "dj",
        description="Entertainment preference (e.g. dj, live_band, acoustic, mc, sound_system, none)",
    )
    event_duration_hours: float = Field(
        default=4.0,
        ge=1.0,
        le=72.0,
        description="Expected duration of the celebration in hours (1 to 72 hours).",
    )
    preferences: Optional[str] = Field(
        None,
        max_length=1500,
        description="Optional natural-language requirements, theme specifics, or VIP requirements",
    )
    title: Optional[str] = Field(
        None,
        max_length=200,
        description="Optional custom title for the saved party plan",
    )

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Event type cannot be empty.")
        normalized = v.strip().lower().replace(" ", "_").replace("-", "_")
        if normalized not in ALLOWED_EVENT_TYPES:
            raise ValueError(
                f"Invalid event_type '{v}'. Allowed types are: {', '.join(ALLOWED_EVENT_TYPES)}"
            )
        return normalized

    @field_validator("venue_type")
    @classmethod
    def validate_venue_type(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Venue type cannot be empty.")
        normalized = v.strip().lower().replace(" ", "_").replace("-", "_")
        if normalized not in ALLOWED_VENUE_TYPES:
            raise ValueError(
                f"Invalid venue_type '{v}'. Allowed types are: {', '.join(ALLOWED_VENUE_TYPES)}"
            )
        return normalized


class PartyCategoryAllocation(BaseModel):
    category: str
    allocated_amount: float
    percentage: float

    model_config = ConfigDict(from_attributes=True)


class PartyPlanDetails(BaseModel):
    event_type: str
    guest_count: int
    venue_type: str
    food_preference: Optional[str] = None
    decoration_preference: Optional[str] = None
    entertainment_preference: Optional[str] = None
    event_duration_hours: float = 4.0
    estimated_food_budget_per_guest: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class PartyPlanResponse(BaseModel):
    module: str = "party"
    source: Literal["gemini", "deterministic_fallback"]
    plan_id: Optional[int] = None
    plan: PartyPlanDetails
    category_allocations: List[PartyCategoryAllocation] = Field(default_factory=list)
    summary: str
    budget_guidance: Optional[str] = None
    recommendations: List[RecommendedItemDetail]
    budget: BudgetSummary
    warnings: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)
