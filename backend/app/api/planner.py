from decimal import Decimal
from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.budget_plan import BudgetItem, BudgetPlan
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.schemas.home_planner import HomePlanRequest, HomePlanResponse
from app.schemas.jewelry_planner import JewelryPlanRequest, JewelryPlanResponse
from app.schemas.party_planner import PartyPlanRequest, PartyPlanResponse
from app.schemas.planner import (
    BudgetPlanRequest,
    BudgetPlanResponse,
    CalculatedItemDetail,
)
from app.services.budget_engine import BudgetEngine
from app.services.home_planner_service import home_planner_service
from app.services.image_storage_service import image_storage_service
from app.services.jewelry_planner_service import jewelry_planner_service
from app.services.party_planner_service import party_planner_service

router = APIRouter()


@router.post(
    "/budget",
    response_model=BudgetPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Deterministic budget plan calculation",
    description=(
        "Calculates item subtotals, total planned cost, remaining budget, and over-budget status. "
        "Authoritative product prices are strictly retrieved from the database. Requires authentication."
    ),
)
def calculate_budget(
    plan_in: BudgetPlanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BudgetPlanResponse:
    # 1. Aggregate duplicate product IDs (summing their quantities predictably)
    aggregated_items: Dict[int, int] = {}
    for item in plan_in.items:
        aggregated_items[item.product_id] = aggregated_items.get(item.product_id, 0) + item.quantity

    product_ids = list(aggregated_items.keys())

    # 2. Query authoritative products and categories from database
    products = (
        db.query(Product)
        .join(Category, Product.category_id == Category.id)
        .filter(Product.id.in_(product_ids))
        .all()
    )
    product_map = {p.id: p for p in products}

    # 3. Verify all requested product IDs exist
    for pid in product_ids:
        if pid not in product_map:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {pid} was not found in catalog.",
            )

    # 4. Enforce strict module isolation (prevent mixing home, party, jewelry)
    target_module = plan_in.module.lower()
    for pid, product in product_map.items():
        product_module = product.category.module_type.lower()
        if product_module != target_module:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Module mismatch: Product '{product.name}' (ID {product.id}) "
                    f"belongs to '{product_module}', but the plan module is '{target_module}'."
                ),
            )

    # 5. Deterministic arithmetic calculation with Decimal
    total_budget_dec = BudgetEngine.to_decimal(plan_in.total_budget)
    calculated_items: List[CalculatedItemDetail] = []
    subtotals_dec: List[Decimal] = []

    for pid in product_ids:
        product = product_map[pid]
        quantity = aggregated_items[pid]
        unit_price_dec = BudgetEngine.to_decimal(product.price)
        subtotal_dec = BudgetEngine.calculate_subtotal(unit_price_dec, quantity)
        subtotals_dec.append(subtotal_dec)

        calculated_items.append(
            CalculatedItemDetail(
                product_id=product.id,
                name=product.name,
                unit_price=float(unit_price_dec),
                quantity=quantity,
                subtotal=float(subtotal_dec),
                category_name=product.category.name if product.category else None,
                module_type=product.category.module_type,
                platform=product.platform,
                is_demo=product.is_demo,
            )
        )

    total_cost_dec = BudgetEngine.calculate_total_cost(subtotals_dec)
    remaining_budget_dec = BudgetEngine.calculate_remaining_budget(total_budget_dec, total_cost_dec)
    over_budget_dec = BudgetEngine.calculate_over_budget_amount(total_budget_dec, total_cost_dec)
    utilization_pct = BudgetEngine.calculate_utilization_percentage(total_budget_dec, total_cost_dec)
    is_within = BudgetEngine.is_within_budget(total_budget_dec, total_cost_dec)

    plan_id = None
    title = plan_in.title or f"{plan_in.module.capitalize()} Budget Plan"

    # 6. Optional persistence into database
    if plan_in.save_plan:
        plan = BudgetPlan(
            user_id=current_user.id,
            title=title,
            module_type=plan_in.module,
            total_budget=float(total_budget_dec),
            allocated_budget=float(total_cost_dec),
            remaining_budget=float(remaining_budget_dec),
            currency=settings.DEFAULT_CURRENCY,
            is_fallback=False,
        )
        db.add(plan)
        db.flush()

        for item_detail in calculated_items:
            budget_item = BudgetItem(
                plan_id=plan.id,
                category_name=item_detail.category_name or "General",
                allocated_amount=item_detail.subtotal,
                spent_amount=item_detail.subtotal,
                priority="medium",
                reason=f"Item: {item_detail.name} (Qty: {item_detail.quantity})",
            )
            db.add(budget_item)

        db.commit()
        db.refresh(plan)
        plan_id = plan.id

    return BudgetPlanResponse(
        module=plan_in.module,
        total_budget=float(total_budget_dec),
        total_cost=float(total_cost_dec),
        remaining_budget=float(remaining_budget_dec),
        over_budget_amount=float(over_budget_dec),
        utilization_percentage=utilization_pct,
        is_within_budget=is_within,
        currency=settings.DEFAULT_CURRENCY,
        currency_symbol=settings.CURRENCY_SYMBOL,
        items=calculated_items,
        plan_id=plan_id,
        title=title,
    )


@router.post(
    "/home",
    response_model=HomePlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Home Interior Budget Planner",
    description=(
        "Generates a personalized home interior budget plan tailored to room type, style, "
        "color palette, and priorities. Combines Gemini GenAI for preference matching with "
        "the deterministic Budget Engine. Persists plan for the user in the database."
    ),
)
def plan_home_interior(
    request: HomePlanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HomePlanResponse:
    return home_planner_service.process_home_plan(
        db=db,
        request=request,
        current_user=current_user,
    )


@router.post(
    "/party",
    response_model=PartyPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Party / Event Budget Planner",
    description=(
        "Generates a personalized party and celebration budget plan tailored to event type, "
        "venue, guest count, food, and entertainment preferences. Combines Gemini GenAI "
        "preference matching with the deterministic Budget Engine. Persists plan for the user in the database."
    ),
)
def plan_party_event(
    request: PartyPlanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PartyPlanResponse:
    return party_planner_service.process_party_plan(
        db=db,
        request=request,
        current_user=current_user,
    )


@router.post(
    "/jewelry",
    response_model=JewelryPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Jewelry Budget Planner",
    description=(
        "Generates a personalized jewelry budget plan tailored to occasion, style, metal, "
        "and color preferences. Supports optional outfit image analysis via Google Gemini multimodal AI. "
        "Enforces strict jewelry catalog isolation, deterministic Budget Engine arithmetic, and persistence."
    ),
)
async def plan_jewelry(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JewelryPlanResponse:
    content_type = request.headers.get("content-type", "").lower()
    image_bytes = None
    image_mime_type = None

    if "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        budget_raw = form.get("budget")
        if budget_raw is None or str(budget_raw).strip() == "":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Missing required 'budget' field.",
            )
        try:
            budget_val = float(budget_raw)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="'budget' must be a valid positive number.",
            )

        occasion_raw = form.get("occasion")
        if not occasion_raw or str(occasion_raw).strip() == "":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Missing required 'occasion' field.",
            )

        payload_dict = {
            "budget": budget_val,
            "occasion": str(occasion_raw).strip(),
            "style": str(form.get("style") or "Traditional").strip(),
            "preferred_metal": str(form.get("preferred_metal") or "gold").strip(),
            "preferred_color": str(form.get("preferred_color")).strip() if form.get("preferred_color") else None,
            "jewelry_type": str(form.get("jewelry_type") or "any").strip(),
            "preferences": str(form.get("preferences")).strip() if form.get("preferences") else None,
            "title": str(form.get("title")).strip() if form.get("title") else None,
        }
        try:
            plan_req = JewelryPlanRequest.model_validate(payload_dict)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e),
            )

        file_obj = form.get("outfit_image")
        if file_obj and hasattr(file_obj, "filename") and file_obj.filename:
            image_bytes, image_mime_type = await image_storage_service.validate_and_read_image(file_obj)

    else:
        # Default JSON payload
        try:
            body_json = await request.json()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid JSON payload.",
            )
        try:
            plan_req = JewelryPlanRequest.model_validate(body_json)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e),
            )

    return jewelry_planner_service.process_jewelry_plan(
        db=db,
        request=plan_req,
        current_user=current_user,
        image_bytes=image_bytes,
        image_mime_type=image_mime_type,
    )



