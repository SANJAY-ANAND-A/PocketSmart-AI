import json
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.budget_plan import BudgetPlan
from app.models.product import Product
from app.models.recommendation import Recommendation
from app.models.user import User
from app.schemas.plans import (
    DeletePlanResponse,
    SavedPlanBudgetItem,
    SavedPlanDetailResponse,
    SavedPlanListItem,
    SavedPlanListResponse,
    SavedPlanRecommendation,
)
from app.services.recommendation_engine import _format_product_response

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_MODULE_FILTERS = ["home", "party", "jewelry"]


@router.get(
    "",
    response_model=SavedPlanListResponse,
    status_code=status.HTTP_200_OK,
    summary="List saved budget plans",
    description=(
        "Retrieves all saved budget plans belonging strictly to the authenticated user. "
        "Supports optional filtering by module (home, party, jewelry)."
    ),
)
def list_saved_plans(
    module: Optional[str] = Query(
        None,
        description="Optional filter by planner module: 'home', 'party', or 'jewelry'.",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SavedPlanListResponse:
    query = (
        db.query(BudgetPlan)
        .options(
            joinedload(BudgetPlan.items),
            joinedload(BudgetPlan.recommendations),
        )
        .filter(BudgetPlan.user_id == current_user.id)
    )

    if module is not None and module.strip():
        norm_module = module.strip().lower()
        if norm_module not in ALLOWED_MODULE_FILTERS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid module filter '{module}'. Allowed values are: {', '.join(ALLOWED_MODULE_FILTERS)}",
            )
        query = query.filter(BudgetPlan.module_type == norm_module)

    plans = query.order_by(BudgetPlan.created_at.desc()).all()

    items: List[SavedPlanListItem] = []
    for p in plans:
        items.append(
            SavedPlanListItem(
                id=p.id,
                title=p.title,
                module_type=p.module_type,
                total_budget=p.total_budget,
                allocated_budget=p.allocated_budget,
                remaining_budget=p.remaining_budget,
                currency=p.currency or settings.DEFAULT_CURRENCY,
                currency_symbol=settings.CURRENCY_SYMBOL,
                is_fallback=p.is_fallback,
                items_count=len(p.items) if p.items else 0,
                recommendations_count=len(p.recommendations) if p.recommendations else 0,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
        )

    return SavedPlanListResponse(items=items, total=len(items))


@router.get(
    "/{plan_id}",
    response_model=SavedPlanDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get detailed saved plan",
    description=(
        "Retrieves a complete saved plan by ID including budget items, catalog recommendations, "
        "and AI strategic notes. Access is strictly scoped to the authenticated owner."
    ),
)
def get_saved_plan(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SavedPlanDetailResponse:
    plan = (
        db.query(BudgetPlan)
        .options(
            joinedload(BudgetPlan.items),
            joinedload(BudgetPlan.recommendations).joinedload(Recommendation.product).joinedload(Product.category),
            joinedload(BudgetPlan.recommendations).joinedload(Recommendation.product).joinedload(Product.vendor),
        )
        .filter(
            BudgetPlan.id == plan_id,
            BudgetPlan.user_id == current_user.id,
        )
        .first()
    )

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget plan with ID {plan_id} not found.",
        )

    # Parse preferences if stored as JSON
    parsed_preferences = None
    if plan.preferences:
        try:
            parsed_preferences = json.loads(plan.preferences)
        except Exception:
            parsed_preferences = {"raw": plan.preferences}

    # Format budget items
    formatted_items = [
        SavedPlanBudgetItem(
            id=item.id,
            category_name=item.category_name,
            allocated_amount=item.allocated_amount,
            spent_amount=item.spent_amount,
            priority=item.priority,
            reason=item.reason,
            created_at=item.created_at,
        )
        for item in (plan.items or [])
    ]

    # Format recommendations with associated product details
    formatted_recommendations = []
    for rec in (plan.recommendations or []):
        formatted_product = _format_product_response(rec.product) if rec.product else None
        formatted_recommendations.append(
            SavedPlanRecommendation(
                id=rec.id,
                product_id=rec.product_id,
                match_score=rec.match_score,
                recommendation_reason=rec.recommendation_reason,
                is_upgrade=rec.is_upgrade,
                product=formatted_product,
            )
        )

    return SavedPlanDetailResponse(
        id=plan.id,
        title=plan.title,
        module_type=plan.module_type,
        total_budget=plan.total_budget,
        allocated_budget=plan.allocated_budget,
        remaining_budget=plan.remaining_budget,
        currency=plan.currency or settings.DEFAULT_CURRENCY,
        currency_symbol=settings.CURRENCY_SYMBOL,
        is_fallback=plan.is_fallback,
        preferences=parsed_preferences,
        ai_reasoning=plan.ai_reasoning,
        items=formatted_items,
        recommendations=formatted_recommendations,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


@router.delete(
    "/{plan_id}",
    response_model=DeletePlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a saved budget plan",
    description=(
        "Deletes a saved budget plan belonging to the authenticated user. "
        "Cascades deletion cleanly to child budget items and recommendations."
    ),
)
def delete_saved_plan(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DeletePlanResponse:
    plan = (
        db.query(BudgetPlan)
        .filter(
            BudgetPlan.id == plan_id,
            BudgetPlan.user_id == current_user.id,
        )
        .first()
    )

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget plan with ID {plan_id} not found.",
        )

    db.delete(plan)
    db.commit()

    return DeletePlanResponse(
        detail="Budget plan deleted successfully.",
        plan_id=plan_id,
    )
