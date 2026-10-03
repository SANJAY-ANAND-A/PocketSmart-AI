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
from app.schemas.jewelry_planner import (
    JewelryCategoryAllocation,
    JewelryPlanDetails,
    JewelryPlanRequest,
    JewelryPlanResponse,
)
from app.schemas.recommendation import BudgetSummary, RecommendedItemDetail
from app.services.budget_engine import BudgetEngine
from app.services.gemini_service import GeminiService, gemini_service
from app.services.recommendation_engine import _format_product_response

logger = logging.getLogger(__name__)

# Standard priority ordering for jewelry set matching
JEWELRY_CATEGORY_PRIORITY = [
    "jewelry-necklace",
    "jewelry-earrings",
    "jewelry-bangles",
    "jewelry-bracelet",
    "jewelry-ring",
    "jewelry-pendant",
]


class JewelryPlannerService:
    """
    Dedicated Service for the Jewelry Budget Planner.
    Enforces strict jewelry module isolation, deterministic financial calculations,
    multimodal outfit image styling with privacy guardrails, and reliable rule-based fallback.
    """

    def __init__(self, ai_service: Optional[GeminiService] = None):
        self.ai_service = ai_service if ai_service is not None else gemini_service

    def calculate_category_allocations(
        self,
        request: JewelryPlanRequest,
    ) -> List[JewelryCategoryAllocation]:
        """
        Deterministically computes category budget allocation percentages based on
        occasion and requested jewelry type.
        Ensures sum(allocated_amount) <= total_budget.
        """
        total_budget_dec = BudgetEngine.to_decimal(request.budget)
        target_type = (request.jewelry_type or "any").lower()

        # Baseline category weights
        weights: Dict[str, float] = {
            "necklace": 35.0,
            "earrings": 25.0,
            "bangles": 15.0,
            "bracelet": 10.0,
            "ring": 10.0,
            "pendant": 5.0,
        }

        if target_type == "necklace":
            weights = {"necklace": 60.0, "earrings": 20.0, "ring": 10.0, "bracelet": 5.0, "bangles": 5.0}
        elif target_type == "earrings":
            weights = {"earrings": 60.0, "necklace": 20.0, "ring": 10.0, "bracelet": 5.0, "bangles": 5.0}
        elif target_type in ["bracelet", "bangles"]:
            weights = {"bangles": 40.0, "bracelet": 30.0, "earrings": 20.0, "ring": 10.0}
        elif target_type == "ring":
            weights = {"ring": 65.0, "earrings": 20.0, "necklace": 15.0}
        elif target_type == "pendant":
            weights = {"pendant": 55.0, "earrings": 25.0, "ring": 20.0}
        elif request.occasion in ["wedding", "traditional_event"]:
            # Bridal / traditional favors bridal necklace choker and kadas
            weights = {"necklace": 50.0, "earrings": 20.0, "bangles": 20.0, "ring": 10.0}
        elif request.occasion in ["formal_event", "party"]:
            # Modern cocktail styling favors studs, solitaire necklaces, and tennis bracelets
            weights = {"necklace": 35.0, "earrings": 25.0, "bracelet": 25.0, "ring": 15.0}

        # Normalize weights to exactly 100%
        total_weight = sum(weights.values())
        allocations: List[JewelryCategoryAllocation] = []
        allocated_sum = Decimal("0.00")

        categories_list = list(weights.keys())
        for idx, cat_name in enumerate(categories_list):
            normalized_pct = (weights[cat_name] / total_weight) * 100.0
            pct_dec = Decimal(str(round(normalized_pct, 2)))

            # For the last category, assign the exact remaining balance to prevent penny rounding errors
            if idx == len(categories_list) - 1:
                cat_amount_dec = total_budget_dec - allocated_sum
                if cat_amount_dec < Decimal("0.00"):
                    cat_amount_dec = Decimal("0.00")
            else:
                cat_amount_dec = (total_budget_dec * (pct_dec / Decimal("100.00"))).quantize(
                    Decimal("0.01")
                )
                allocated_sum += cat_amount_dec

            allocations.append(
                JewelryCategoryAllocation(
                    category=cat_name,
                    allocated_amount=float(cat_amount_dec),
                    percentage=round(normalized_pct, 1),
                )
            )

        return allocations

    def get_jewelry_candidates(
        self,
        db: Session,
        request: JewelryPlanRequest,
        limit: int = 25,
    ) -> List[Product]:
        """
        Retrieves candidate products STRICTLY belonging to the 'jewelry' module.
        Ensures home and party catalog items are never included.
        """
        query = (
            db.query(Product)
            .options(joinedload(Product.category), joinedload(Product.vendor))
            .join(Category, Product.category_id == Category.id)
            .filter(
                Category.module_type == "jewelry",
                Product.availability == True,
            )
        )

        candidates = query.all()

        # Score candidates based on occasion, style, metal, color, and jewelry type
        def candidate_sort_key(p: Product) -> float:
            score = p.rating
            slug = p.category.slug if p.category else ""
            cat_name = p.category.name.lower() if p.category else ""
            desc = (p.description or "").lower()
            tags = (p.tags or "").lower()
            name = p.name.lower()
            style = (p.style or "").lower()

            # Target jewelry type match
            target_type = (request.jewelry_type or "any").lower()
            if target_type != "any" and (target_type in slug or target_type in cat_name or target_type in tags):
                score += 5.0

            # Style match
            if request.style and request.style.lower() in style:
                score += 3.5

            # Occasion match
            if request.occasion.lower() in tags or request.occasion.lower() in desc:
                score += 3.0

            # Metal preference match
            metal = (request.preferred_metal or "any").lower()
            if metal != "any" and (metal in tags or metal in desc or metal in name):
                score += 3.0

            # Color preference match
            if request.preferred_color and (
                request.preferred_color.lower() in tags or request.preferred_color.lower() in desc
            ):
                score += 2.5

            return score

        sorted_candidates = sorted(candidates, key=candidate_sort_key, reverse=True)
        return sorted_candidates[:limit]

    def _generate_jewelry_fallback(
        self,
        db: Session,
        request: JewelryPlanRequest,
        candidates: List[Product],
    ) -> Tuple[List[Tuple[Product, int, str]], List[str]]:
        """
        Deterministic rule-based fallback for Jewelry Planner.
        Greedily selects top jewelry pieces across balanced categories within budget.
        """
        budget_dec = BudgetEngine.to_decimal(request.budget)
        selected: List[Tuple[Product, int, str]] = []
        warnings = ["AI recommendations are temporarily unavailable. Showing rule-based recommendations."]
        current_cost = Decimal("0.00")
        used_cats = set()

        # Group candidates by category slug
        by_category: Dict[str, List[Product]] = {}
        for p in candidates:
            slug = p.category.slug if p.category else "jewelry-misc"
            by_category.setdefault(slug, []).append(p)

        target_type = (request.jewelry_type or "any").lower()

        # If a specific jewelry type is requested, try to select that first
        if target_type != "any":
            for cat_slug, prods in by_category.items():
                if target_type in cat_slug:
                    for prod in prods:
                        price_dec = BudgetEngine.to_decimal(prod.price)
                        if current_cost + price_dec <= budget_dec:
                            selected.append((
                                prod,
                                1,
                                f"Selected as the primary {prod.category.name if prod.category else 'jewelry'} "
                                f"matching your '{request.style or 'traditional'}' aesthetic.",
                            ))
                            current_cost += price_dec
                            used_cats.add(cat_slug)
                            break
                    break

        # Complement with remaining priority jewelry categories
        for cat_slug in JEWELRY_CATEGORY_PRIORITY:
            if cat_slug in used_cats:
                continue
            cat_products = by_category.get(cat_slug, [])
            for prod in cat_products:
                price_dec = BudgetEngine.to_decimal(prod.price)
                if current_cost + price_dec <= budget_dec:
                    selected.append((
                        prod,
                        1,
                        f"Complementary piece for {request.occasion.replace('_', ' ')}: "
                        f"rated {prod.rating}★ with {prod.style or 'classic'} styling.",
                    ))
                    current_cost += price_dec
                    used_cats.add(cat_slug)
                    break

            if len(selected) >= 4:
                break

        # If nothing could be afforded, select the single most accessible candidate
        if not selected and candidates:
            cheapest = min(candidates, key=lambda p: p.price)
            selected.append((
                cheapest,
                1,
                f"Selected as the most accessible starter piece in the jewelry catalog.",
            ))

        return selected, warnings

    def process_jewelry_plan(
        self,
        db: Session,
        request: JewelryPlanRequest,
        current_user: User,
        image_bytes: Optional[bytes] = None,
        image_mime_type: Optional[str] = None,
    ) -> JewelryPlanResponse:
        """
        Executes end-to-end Jewelry Planning:
        1. Query jewelry-only candidate products from SQLite.
        2. Deterministically calculate category allocations.
        3. Format rich jewelry and occasion context for Gemini (with optional outfit image).
        4. Call Gemini (or fallback).
        5. Validate product IDs, module consistency & prices against SQLite.
        6. Run deterministic budget engine & safety adjustment.
        7. Persist plan, items, and recommendations to database.
        8. Return structured JewelryPlanResponse.
        """
        candidates = self.get_jewelry_candidates(db, request)
        budget_dec = BudgetEngine.to_decimal(request.budget)

        # Calculate category allocations
        category_allocations = self.calculate_category_allocations(request)

        # Construct comprehensive preference text
        pref_parts = [
            f"Occasion: {request.occasion.replace('_', ' ').title()}",
            f"Preferred Style: {request.style or 'Traditional'}",
        ]
        if request.preferred_metal and request.preferred_metal != "any":
            pref_parts.append(f"Preferred Metal: {request.preferred_metal.title()}")
        if request.preferred_color:
            pref_parts.append(f"Preferred Accent Color: {request.preferred_color.title()}")
        if request.jewelry_type and request.jewelry_type != "any":
            pref_parts.append(f"Target Jewelry Type: {request.jewelry_type.title()}")
        if request.preferences:
            pref_parts.append(f"Additional Requirements: {request.preferences}")

        full_preferences_text = ". ".join(pref_parts)

        source: str = "gemini"
        warnings: List[str] = []
        raw_selections: List[Tuple[Product, int, str]] = []
        summary = ""
        budget_guidance = None
        has_image = bool(image_bytes and image_mime_type)

        gemini_result = None
        if self.ai_service.is_available() and candidates:
            try:
                gemini_result = self.ai_service.generate_recommendations(
                    module="jewelry",
                    budget=request.budget,
                    preferences=full_preferences_text,
                    candidates=candidates,
                    image_bytes=image_bytes,
                    image_mime_type=image_mime_type,
                )
            except Exception as e:
                logger.warning(f"Gemini jewelry recommendation call failed: {e}. Gracefully falling back.")
                gemini_result = None

        if gemini_result and gemini_result.recommendations:
            candidate_map = {p.id: p for p in candidates}
            for rec in gemini_result.recommendations:
                prod = candidate_map.get(rec.product_id)
                if prod is not None:
                    raw_selections.append((prod, rec.quantity, rec.reason))
                else:
                    # Check if the product exists in the database but belongs to another module
                    other_prod = (
                        db.query(Product)
                        .join(Category, Product.category_id == Category.id)
                        .filter(Product.id == rec.product_id)
                        .first()
                    )
                    if other_prod and other_prod.category and other_prod.category.module_type != "jewelry":
                        warnings.append(
                            f"Omitted product ID {rec.product_id} due to non-jewelry module mismatch ({other_prod.category.module_type})."
                        )
                    else:
                        warnings.append(
                            f"AI-recommended jewelry ID {rec.product_id} was omitted because it was not in the catalog."
                        )

            if raw_selections:
                summary = gemini_result.summary
                budget_guidance = gemini_result.budget_guidance
                if gemini_result.warnings:
                    warnings.extend(gemini_result.warnings)
            else:
                logger.warning("Gemini returned zero valid jewelry IDs. Triggering fallback.")
                source = "deterministic_fallback"
                raw_selections, fb_warnings = self._generate_jewelry_fallback(db, request, candidates)
                warnings.extend(fb_warnings)
                summary = (
                    f"Rule-based jewelry plan curated for your {request.occasion.replace('_', ' ')} "
                    f"within ₹{request.budget:,.2f}."
                )
                budget_guidance = "Prioritize the centerpiece necklace or earrings before adding accent rings."
        else:
            source = "deterministic_fallback"
            raw_selections, fb_warnings = self._generate_jewelry_fallback(db, request, candidates)
            warnings.extend(fb_warnings)
            summary = (
                f"Rule-based jewelry plan curated for your {request.occasion.replace('_', ' ')} "
                f"within ₹{request.budget:,.2f}."
            )
            budget_guidance = "Prioritize the centerpiece necklace or earrings before adding accent rings."

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
            # Sort discretionary items by total item subtotal descending to prune most expensive first
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

        plan_title = (
            request.title
            or f"{request.occasion.replace('_', ' ').title()} {request.style or 'Custom'} Jewelry Plan"
        )

        # -------------------------------------------------------------
        # Database Persistence: BudgetPlan, BudgetItem, Recommendation
        # -------------------------------------------------------------
        stored_preferences = request.model_dump()
        stored_preferences["has_outfit_image"] = has_image

        plan_record = BudgetPlan(
            user_id=current_user.id,
            title=plan_title,
            module_type="jewelry",
            total_budget=float(budget_dec),
            allocated_budget=float(final_total_cost),
            remaining_budget=float(remaining_budget),
            currency=settings.DEFAULT_CURRENCY,
            preferences=json.dumps(stored_preferences),
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

        return JewelryPlanResponse(
            module="jewelry",
            source=source,
            plan=JewelryPlanDetails(
                occasion=request.occasion,
                style=request.style,
                preferred_metal=request.preferred_metal,
                preferred_color=request.preferred_color,
                jewelry_type=request.jewelry_type,
                outfit_analyzed=has_image,
            ),
            category_allocations=category_allocations,
            summary=summary,
            budget_guidance=budget_guidance,
            recommendations=recommended_items,
            budget=budget_summary,
            warnings=warnings,
            plan_id=plan_record.id,
        )


jewelry_planner_service = JewelryPlannerService()
