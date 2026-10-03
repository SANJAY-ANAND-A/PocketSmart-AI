from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
from app.services.recommendation_engine import recommendation_engine

router = APIRouter()


@router.post(
    "",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate AI-powered budget plan and recommendations",
    description=(
        "Interprets natural language preferences using Google Gemini AI, selects candidate catalog products, "
        "and validates final allocations using the deterministic budget engine. "
        "Gracefully falls back to rule-based catalog ranking if Gemini is unavailable or rate-limited."
    ),
)
def create_recommendations(
    request: RecommendationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecommendationResponse:
    return recommendation_engine.process_recommendation_request(
        db=db,
        request=request,
        current_user=current_user,
    )
