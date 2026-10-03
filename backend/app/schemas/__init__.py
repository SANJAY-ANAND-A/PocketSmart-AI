"""Pydantic Schemas for PocketSmart AI"""

from app.schemas.user import (
    UserBase,
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    TokenPayload,
)
from app.schemas.catalog import (
    CategoryResponse,
    VendorResponse,
    ProductResponse,
    ProductListResponse,
)
from app.schemas.planner import (
    BudgetItemInput,
    BudgetPlanRequest,
    CalculatedItemDetail,
    BudgetPlanResponse,
)
from app.schemas.recommendation import (
    GeminiProductRec,
    GeminiInterpretedPreferences,
    GeminiStructuredResponse,
    RecommendationRequest,
    RecommendedItemDetail,
    BudgetSummary,
    RecommendationResponse,
)
from app.schemas.home_planner import (
    ALLOWED_ROOM_TYPES,
    HomePlanRequest,
    HomePlanDetails,
    HomePlanResponse,
)

__all__ = [
    "UserBase",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "Token",
    "TokenPayload",
    "CategoryResponse",
    "VendorResponse",
    "ProductResponse",
    "ProductListResponse",
    "BudgetItemInput",
    "BudgetPlanRequest",
    "CalculatedItemDetail",
    "BudgetPlanResponse",
    "GeminiProductRec",
    "GeminiInterpretedPreferences",
    "GeminiStructuredResponse",
    "RecommendationRequest",
    "RecommendedItemDetail",
    "BudgetSummary",
    "RecommendationResponse",
    "ALLOWED_ROOM_TYPES",
    "HomePlanRequest",
    "HomePlanDetails",
    "HomePlanResponse",
]
