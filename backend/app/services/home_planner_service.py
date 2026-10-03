import json
import logging
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from app.core.config import settings
from app.models.budget_plan import BudgetItem, BudgetPlan
from app.models.category import Category
from app.models.product import Product
from app.models.recommendation import Recommendation
from app.models.user import User
from app.schemas.home_planner import (
    HomePlanDetails,
    HomePlanRequest,
    HomePlanResponse,
)
from app.schemas.recommendation import BudgetSummary, RecommendedItemDetail
from app.services.budget_engine import BudgetEngine
from app.services.gemini_service import GeminiService, gemini_service
from app.services.recommendation_engine import _format_product_response

logger = logging.getLogger(__name__)

# Map typical room types to priority furniture categories
ROOM_CATEGORY_PREFERENCES = {
    "bedroom": ["Bed", "Wardrobe", "Table", "Lighting", "Curtains", "Storage"],
    "living_room": ["Sofa", "Table", "Lighting", "Decor", "Curtains", "Storage"],
    "dining_room": ["Table", "Chair", "Lighting", "Storage", "Decor"],
    "home_office": ["Table", "Chair", "Lighting", "Storage", "Decor"],
    "kitchen": ["Storage", "Lighting", "Table", "Decor"],
    "studio": ["Bed", "Sofa", "Table", "Wardrobe", "Lighting", "Storage"],
    "balcony": ["Chair", "Table", "Lighting", "Decor"],
}


class HomePlannerService:
    """
    Dedicated Service for the Home Interior Budget Planner.
    Enforces strict home module isolation, deterministic financial calculations,
    preference interpretation with Gemini AI, and reliable rule-based fallback.
    """

    def __init__(self, ai_service: Optional[GeminiService] = None):
        self.ai_service = ai_service if ai_service is not None else gemini_service

    def get_home_candidates(
        self,
        db: Session,
        room_type: str,
        style: Optional[str] = None,
        limit: int = 25,
    ) -> List[Product]:
        """
        Retrieves candidate products STRICTLY belonging to the 'home' module.
        Ensures party and jewelry catalog items are never considered.
        """
        query = (
            db.query(Product)
            .options(joinedload(Product.category), joinedload(Product.vendor))
            .join(Category, Product.category_id == Category.id)
            .filter(
                Category.module_type == "home",
                Product.availability == True,
            )
        )

        candidates = query.all()

        # Score and prioritize candidates based on room relevance and style
        preferred_cats = ROOM_CATEGORY_PREFERENCES.get(room_type.lower(), [])

        def candidate_sort_key(p: Product) -> float:
            score = p.rating
            cat_name = p.category.name if p.category else ""
            if cat_name in preferred_cats:
                # Rank priority categories higher
                idx = preferred_cats.index(cat_name)
                score += (len(preferred_cats) - idx) * 2.0
            if style and p.style and style.lower() in p.style.lower():
                score += 3.0
            return score

        sorted_candidates = sorted(candidates, key=candidate_sort_key, reverse=True)
        return sorted_candidates[:limit]

    def _generate_home_fallback(
        self,
        db: Session,
        request: HomePlanRequest,
        candidates: List[Product],
    ) -> Tuple[List[Tuple[Product, int, str]], List[str]]:
        """
        Deterministic rule-based fallback for Home Interior Planner.
        Greedily selects top priority furniture items matching room type within budget.
        """
        preferred_cats = ROOM_CATEGORY_PREFERENCES.get(request.room_type, [])
        budget_dec = BudgetEngine.to_decimal(request.budget)

        selected: List[Tuple[Product, int, str]] = []
        current_cost = Decimal("0.00")
        used_cats = set()

        for prod in candidates:
            cat_name = prod.category.name if prod.category else ""
            price_dec = BudgetEngine.to_decimal(prod.price)

            # Ensure diversity across key room categories
            if cat_name not in used_cats or len(selected) < 2:
                if current_cost + price_dec <= budget_dec:
                    selected.append((
                        prod,
                        1,
                        f"Recommended for {request.room_type.replace('_', ' ')}: high rating ({prod.rating}★) and style match ({prod.style or 'Contemporary'}).",
                    ))
                    current_cost += price_dec
                    used_cats.add(cat_name)

            if len(selected) >= 4:
                break

        if not selected and candidates:
            cheapest = min(candidates, key=lambda p: p.price)
            selected.append((
                cheapest,
                1,
                f"Selected as the most accessible starter piece for your {request.room_type}.",
            ))

        warnings = ["AI recommendations are temporarily unavailable. Showing rule-based recommendations."]
        return selected, warnings

    def process_home_plan(
        self,
        db: Session,
        request: HomePlanRequest,
        current_user: User,
    ) -> HomePlanResponse:
        """
        Executes end-to-end Home Interior Planning:
        1. Query home-only candidates from SQLite.
        2. Format rich room context for Gemini.
        3. Call Gemini (or fallback).
        4. Validate product IDs & prices against SQLite.
        5. Run deterministic budget engine & safety adjustment.
        6. Persist plan, items, and recommendations to database.
        7. Return structured HomePlanResponse.
        """
        candidates = self.get_home_candidates(db, request.room_type, request.style)
        budget_dec = BudgetEngine.to_decimal(request.budget)

        # Construct comprehensive user preference prompt
        pref_parts = [
            f"Room Type: {request.room_type.replace('_', ' ').title()}",
            f"Preferred Style: {request.style or 'Modern Minimalist'}",
        ]
        if request.color_preferences:
            pref_parts.append(f"Color Preferences: {', '.join(request.color_preferences)}")
        if request.priorities:
            pref_parts.append(f"Key Priorities: {', '.join(request.priorities)}")
        if request.required_items:
            pref_parts.append(f"Must-Have Items: {', '.join(request.required_items)}")
        if request.preferences:
            pref_parts.append(f"Additional Guidance: {request.preferences}")

        full_preferences_text = ". ".join(pref_parts)

        source: str = "gemini"
        warnings: List[str] = []
        raw_selections: List[Tuple[Product, int, str]] = []
        summary = ""
        budget_guidance = None

        gemini_result = None
        if self.ai_service.is_available() and candidates:
            gemini_result = self.ai_service.generate_recommendations(
                module="home",
                budget=request.budget,
                preferences=full_preferences_text,
                candidates=candidates,
            )

        if gemini_result and gemini_result.recommendations:
            candidate_map = {p.id: p for p in candidates}
            for rec in gemini_result.recommendations:
                prod = candidate_map.get(rec.product_id)
                if prod is not None:
                    raw_selections.append((prod, rec.quantity, rec.reason))
                else:
                    # Check if the product exists in the database but belongs to a different module
                    other_prod = (
                        db.query(Product)
                        .join(Category, Product.category_id == Category.id)
                        .filter(Product.id == rec.product_id)
                        .first()
                    )
                    if other_prod and other_prod.category and other_prod.category.module_type != "home":
                        warnings.append(
                            f"Omitted product ID {rec.product_id} due to non-home module mismatch ({other_prod.category.module_type})."
                        )
                    else:
                        warnings.append(
                            f"AI-recommended product ID {rec.product_id} was omitted because it was not in the catalog."
                        )

            if raw_selections:
                summary = gemini_result.summary
                budget_guidance = gemini_result.budget_guidance
                if gemini_result.warnings:
                    warnings.extend(gemini_result.warnings)
            else:
                logger.warning("Gemini returned zero valid home product IDs. Triggering fallback.")
                source = "deterministic_fallback"
                raw_selections, fb_warnings = self._generate_home_fallback(db, request, candidates)
                warnings.extend(fb_warnings)
                summary = f"Rule-based interior plan curated for your {request.room_type.replace('_', ' ')} within ₹{request.budget:,.2f}."
                budget_guidance = "Focus on the primary furniture items first before adding accents."
        else:
            source = "deterministic_fallback"
            raw_selections, fb_warnings = self._generate_home_fallback(db, request, candidates)
            warnings.extend(fb_warnings)
            summary = f"Rule-based interior plan curated for your {request.room_type.replace('_', ' ')} within ₹{request.budget:,.2f}."
            budget_guidance = "Focus on the primary furniture items first before adding accents."

        # -------------------------------------------------------------
        # Deterministic Budget Enforcement & Safety Trimming
        # -------------------------------------------------------------
        def calc_total(items: List[Tuple[Product, int, str]]) -> Decimal:
            subtotals = [
                BudgetEngine.calculate_subtotal(BudgetEngine.to_decimal(p.price), qty)
                for p, qty, _ in items
            ]
            return BudgetEngine.calculate_total_cost(subtotals)

        adjusted_selections: List[Tuple[Product, int, str]] = list(raw_selections)
        total_cost_dec = calc_total(adjusted_selections)

        if total_cost_dec > budget_dec and len(adjusted_selections) > 1:
            # Sort by item subtotal descending to prune most expensive overflow item first
            adjusted_selections.sort(
                key=lambda item: BudgetEngine.to_decimal(item[0].price) * item[1],
                reverse=True,
            )
            while total_cost_dec > budget_dec and len(adjusted_selections) > 1:
                removed_item = adjusted_selections.pop(0)
                total_cost_dec = calc_total(adjusted_selections)
                warnings.append(
                    f"Trimmed '{removed_item[0].name}' to satisfy your budget limit of ₹{request.budget:,.2f}."
                )

        recommended_items: List[RecommendedItemDetail] = []
        subtotals_dec: List[Decimal] = []

        for prod, qty, reason in adjusted_selections:
            unit_price_dec = BudgetEngine.to_decimal(prod.price)
            subtotal_dec = BudgetEngine.calculate_subtotal(unit_price_dec, qty)
            subtotals_dec.append(subtotal_dec)

            recommended_items.append(
                RecommendedItemDetail(
                    product=_format_product_response(prod),
                    quantity=qty,
                    subtotal=float(subtotal_dec),
                    reason=reason,
                )
            )

        final_total_cost = BudgetEngine.calculate_total_cost(subtotals_dec)
        remaining_budget = BudgetEngine.calculate_remaining_budget(budget_dec, final_total_cost)
        over_budget_amt = BudgetEngine.calculate_over_budget_amount(budget_dec, final_total_cost)
        utilization_pct = BudgetEngine.calculate_utilization_percentage(budget_dec, final_total_cost)
        is_within = BudgetEngine.is_within_budget(budget_dec, final_total_cost)

        budget_summary = BudgetSummary(
            total_budget=float(budget_dec),
            total_cost=float(final_total_cost),
            remaining_budget=float(remaining_budget),
            is_within_budget=is_within,
            over_budget_amount=float(over_budget_amt),
            utilization_percentage=utilization_pct,
            currency=settings.DEFAULT_CURRENCY,
            currency_symbol=settings.CURRENCY_SYMBOL,
        )

        plan_title = request.title or f"{request.style or 'Modern'} {request.room_type.replace('_', ' ').title()} Plan"

        # -------------------------------------------------------------
        # Database Persistence: BudgetPlan, BudgetItem, Recommendation
        # -------------------------------------------------------------
        plan_record = BudgetPlan(
            user_id=current_user.id,
            title=plan_title,
            module_type="home",
            total_budget=float(budget_dec),
            allocated_budget=float(final_total_cost),
            remaining_budget=float(remaining_budget),
            currency=settings.DEFAULT_CURRENCY,
            preferences=json.dumps(request.model_dump()),
            ai_reasoning=summary,
            is_fallback=(source == "deterministic_fallback"),
        )
        db.add(plan_record)
        db.flush()

        for item_detail in recommended_items:
            budget_item = BudgetItem(
                plan_id=plan_record.id,
                category_name=item_detail.product.category_name or "General",
                allocated_amount=item_detail.subtotal,
                spent_amount=item_detail.subtotal,
                priority="high",
                reason=item_detail.reason,
            )
            db.add(budget_item)

            rec_record = Recommendation(
                plan_id=plan_record.id,
                product_id=item_detail.product.id,
                match_score=round(item_detail.product.rating / 5.0, 2),
                recommendation_reason=item_detail.reason,
                is_upgrade=False,
            )
            db.add(rec_record)

        db.commit()
        db.refresh(plan_record)

        return HomePlanResponse(
            module="home",
            source=source,
            plan=HomePlanDetails(
                room_type=request.room_type,
                style=request.style,
                colors=request.color_preferences,
                priorities=request.priorities,
                required_items=request.required_items,
            ),
            summary=summary,
            budget_guidance=budget_guidance,
            recommendations=recommended_items,
            budget=budget_summary,
            warnings=warnings,
            plan_id=plan_record.id,
        )


home_planner_service = HomePlannerService()
