import json
import logging
import math
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from app.core.config import settings
from app.models.budget_plan import BudgetItem, BudgetPlan
from app.models.category import Category
from app.models.product import Product
from app.models.recommendation import Recommendation
from app.models.user import User
from app.schemas.party_planner import (
    PartyCategoryAllocation,
    PartyPlanDetails,
    PartyPlanRequest,
    PartyPlanResponse,
)
from app.schemas.recommendation import BudgetSummary, RecommendedItemDetail
from app.services.budget_engine import BudgetEngine
from app.services.gemini_service import GeminiService, gemini_service
from app.services.recommendation_engine import _format_product_response

logger = logging.getLogger(__name__)

# Standard priority of categories for party event planning
PARTY_CATEGORY_ORDER = [
    "party-venue",
    "party-food",
    "party-decoration",
    "party-entertainment",
    "party-photography",
    "party-misc",
    "party-transportation",
]


class PartyPlannerService:
    """
    Dedicated Service for the Party / Event Budget Planner.
    Enforces strict party module isolation, deterministic financial calculations,
    guest-count scaling, preference interpretation with Gemini AI, and reliable rule-based fallback.
    """

    def __init__(self, ai_service: Optional[GeminiService] = None):
        self.ai_service = ai_service if ai_service is not None else gemini_service

    def calculate_category_allocations(
        self,
        request: PartyPlanRequest,
    ) -> List[PartyCategoryAllocation]:
        """
        Deterministically computes category budget allocation percentages based on
        event type, venue type, entertainment preference, and guest count.
        Ensures sum(allocated_amount) <= total_budget.
        """
        total_budget_dec = BudgetEngine.to_decimal(request.budget)

        # Baseline weights
        weights: Dict[str, float] = {
            "food": 36.0,
            "venue": 24.0,
            "decoration": 12.0,
            "entertainment": 10.0,
            "photography": 10.0,
            "transportation": 4.0,
            "miscellaneous": 4.0,
        }

        # Venue adjustment: Free/low-cost venues shift allocation to food & decor
        if request.venue_type in ["home", "college_campus"]:
            saved_venue = weights["venue"] - 4.0  # Keep 4% for home/campus setup
            weights["venue"] = 4.0
            weights["food"] += saved_venue * 0.6
            weights["decoration"] += saved_venue * 0.4
        elif request.venue_type in ["hotel", "banquet_hall"]:
            # Grand venues take slightly more
            weights["venue"] = 28.0
            weights["food"] = 34.0
            weights["transportation"] = 2.0
            weights["miscellaneous"] = 4.0

        # Entertainment adjustment: if none requested, redistribute
        if request.entertainment_preference and request.entertainment_preference.lower() in ["none", "no"]:
            saved_ent = weights["entertainment"]
            weights["entertainment"] = 0.0
            weights["food"] += saved_ent * 0.6
            weights["decoration"] += saved_ent * 0.4

        # Wedding or Anniversary adjustments: boost photography and decor
        if request.event_type in ["wedding", "anniversary"]:
            weights["photography"] += 3.0
            weights["decoration"] += 2.0
            weights["food"] -= 3.0
            weights["venue"] -= 2.0

        # Normalize weights to exactly 100%
        total_weight = sum(weights.values())
        allocations: List[PartyCategoryAllocation] = []
        allocated_sum = Decimal("0.00")

        categories_list = list(weights.keys())
        for idx, cat_name in enumerate(categories_list):
            normalized_pct = (weights[cat_name] / total_weight) * 100.0
            pct_dec = Decimal(str(round(normalized_pct, 2)))

            # For the last category, assign the exact remaining balance to avoid float/penny rounding errors
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
                PartyCategoryAllocation(
                    category=cat_name,
                    allocated_amount=float(cat_amount_dec),
                    percentage=round(normalized_pct, 1),
                )
            )

        return allocations

    def get_party_candidates(
        self,
        db: Session,
        request: PartyPlanRequest,
        limit: int = 25,
    ) -> List[Product]:
        """
        Retrieves candidate products/services STRICTLY belonging to the 'party' module.
        Ensures home and jewelry items are never included.
        """
        query = (
            db.query(Product)
            .options(joinedload(Product.category), joinedload(Product.vendor))
            .join(Category, Product.category_id == Category.id)
            .filter(
                Category.module_type == "party",
                Product.availability == True,
            )
        )

        candidates = query.all()

        # Score and prioritize candidates based on event requirements
        def candidate_sort_key(p: Product) -> float:
            score = p.rating
            slug = p.category.slug if p.category else ""
            desc = (p.description or "").lower()
            tags = (p.tags or "").lower()
            name = p.name.lower()
            style = (p.style or "").lower()

            # Event type relevance
            if request.event_type in tags or request.event_type in desc:
                score += 3.0

            # Venue type relevance
            if slug == "party-venue":
                if request.venue_type in ["home", "college_campus"]:
                    score -= 5.0  # Deprioritize large commercial venues for home/campus
                elif request.venue_type in tags or request.venue_type in desc:
                    score += 4.0

            # Food preference relevance
            if slug == "party-food":
                if request.food_preference and (
                    request.food_preference.lower() in desc or request.food_preference.lower() in tags
                ):
                    score += 3.5

            # Decoration preference relevance
            if slug == "party-decoration":
                if request.decoration_preference and (
                    request.decoration_preference.lower() in desc
                    or request.decoration_preference.lower() in tags
                    or request.decoration_preference.lower() in style
                ):
                    score += 3.0

            # Entertainment preference relevance
            if slug == "party-entertainment":
                if request.entertainment_preference and request.entertainment_preference.lower() in [
                    "none",
                    "no",
                ]:
                    score -= 10.0
                elif request.entertainment_preference and request.entertainment_preference.lower() in tags:
                    score += 3.0

            return score

        sorted_candidates = sorted(candidates, key=candidate_sort_key, reverse=True)
        return sorted_candidates[:limit]

    def _determine_guest_scaled_quantity(
        self,
        prod: Product,
        guest_count: int,
        budget_dec: Decimal,
        current_total_dec: Decimal,
    ) -> Tuple[int, Optional[str]]:
        """
        Determines item quantity based on guest count (e.g. 50-guest buffet catering,
        100-pack tableware). Checks budget ceiling and caps deterministically if needed.
        """
        cat_slug = prod.category.slug if prod.category else ""
        name_lower = prod.name.lower()
        desc_lower = (prod.description or "").lower()
        tags_lower = (prod.tags or "").lower()

        base_qty = 1
        warning = None

        if cat_slug == "party-food" and ("50" in name_lower or "50-guests" in tags_lower or "buffet" in desc_lower):
            # Catering package sized per 50 guests
            desired_qty = max(1, math.ceil(guest_count / 50))
            unit_price_dec = BudgetEngine.to_decimal(prod.price)
            # Check if desired quantity fits within total budget
            if current_total_dec + (unit_price_dec * desired_qty) > budget_dec:
                # Cap to what fits
                affordable_qty = max(1, int((budget_dec - current_total_dec) // unit_price_dec))
                if affordable_qty < desired_qty:
                    warning = (
                        f"Adjusted catering quantity for '{prod.name}' from {desired_qty} to {affordable_qty} "
                        f"package(s) to strictly respect your ₹{budget_dec:,.2f} total budget."
                    )
                base_qty = max(1, affordable_qty)
            else:
                base_qty = desired_qty

        elif cat_slug == "party-misc" and ("100" in name_lower or "100 sets" in desc_lower or "tableware" in name_lower):
            # Tableware pack sized per 100 guests
            desired_qty = max(1, math.ceil(guest_count / 100))
            unit_price_dec = BudgetEngine.to_decimal(prod.price)
            if current_total_dec + (unit_price_dec * desired_qty) > budget_dec:
                base_qty = 1
                warning = f"Capped tableware sets for '{prod.name}' to 1 pack to stay within budget."
            else:
                base_qty = desired_qty

        return base_qty, warning

    def _generate_party_fallback(
        self,
        db: Session,
        request: PartyPlanRequest,
        candidates: List[Product],
    ) -> Tuple[List[Tuple[Product, int, str]], List[str]]:
        """
        Deterministic rule-based fallback for Party Planner.
        Greedily selects essential party services in balanced priority order within budget.
        """
        budget_dec = BudgetEngine.to_decimal(request.budget)
        selected: List[Tuple[Product, int, str]] = []
        warnings = ["AI recommendations are temporarily unavailable. Showing rule-based recommendations."]
        current_cost = Decimal("0.00")
        used_cats = set()

        # Categorize candidates by category slug
        by_category: Dict[str, List[Product]] = {}
        for p in candidates:
            slug = p.category.slug if p.category else "party-misc"
            by_category.setdefault(slug, []).append(p)

        # Select one item per category following standard priority
        for cat_slug in PARTY_CATEGORY_ORDER:
            # Skip commercial venue rental if hosting at home or campus
            if cat_slug == "party-venue" and request.venue_type in ["home", "college_campus"]:
                continue

            # Skip entertainment if user explicitly requested none
            if cat_slug == "party-entertainment" and request.entertainment_preference in ["none", "no"]:
                continue

            cat_products = by_category.get(cat_slug, [])
            for prod in cat_products:
                qty, qty_warn = self._determine_guest_scaled_quantity(
                    prod, request.guest_count, budget_dec, current_cost
                )
                if qty_warn:
                    warnings.append(qty_warn)

                subtotal = BudgetEngine.calculate_subtotal(BudgetEngine.to_decimal(prod.price), qty)

                if current_cost + subtotal <= budget_dec:
                    selected.append((
                        prod,
                        qty,
                        f"Rule-based recommendation for {cat_slug.replace('party-', '').title()}: "
                        f"rated {prod.rating}★ from {prod.platform}.",
                    ))
                    current_cost += subtotal
                    used_cats.add(cat_slug)
                    break

            if len(selected) >= 5:
                break

        # If nothing could be afforded, select the single most affordable candidate
        if not selected and candidates:
            cheapest = min(candidates, key=lambda p: p.price)
            selected.append((
                cheapest,
                1,
                f"Selected as the most accessible starter service for your {request.event_type}.",
            ))

        return selected, warnings

    def process_party_plan(
        self,
        db: Session,
        request: PartyPlanRequest,
        current_user: User,
    ) -> PartyPlanResponse:
        """
        Executes end-to-end Party / Event Planning:
        1. Query party-only candidate products/services from SQLite.
        2. Deterministically calculate category allocations.
        3. Format rich event context for Gemini.
        4. Call Gemini (or fallback).
        5. Validate product IDs, module consistency & prices against SQLite.
        6. Apply guest-count scaling.
        7. Run deterministic budget engine & safety adjustment.
        8. Persist plan, items, and recommendations to database.
        9. Return structured PartyPlanResponse.
        """
        candidates = self.get_party_candidates(db, request)
        budget_dec = BudgetEngine.to_decimal(request.budget)

        # Calculate category breakdown
        category_allocations = self.calculate_category_allocations(request)
        food_alloc = next((c.allocated_amount for c in category_allocations if c.category == "food"), 0.0)
        food_per_guest = round(food_alloc / request.guest_count, 2) if request.guest_count > 0 else 0.0

        # Construct comprehensive user preference prompt
        pref_parts = [
            f"Event Type: {request.event_type.replace('_', ' ').title()}",
            f"Expected Guests: {request.guest_count}",
            f"Venue Type: {request.venue_type.replace('_', ' ').title()}",
            f"Event Duration: {request.event_duration_hours} hours",
        ]
        if request.food_preference:
            pref_parts.append(f"Food Preference: {request.food_preference}")
        if request.decoration_preference:
            pref_parts.append(f"Decoration Style: {request.decoration_preference}")
        if request.entertainment_preference:
            pref_parts.append(f"Entertainment Preference: {request.entertainment_preference}")
        if request.preferences:
            pref_parts.append(f"Additional Details: {request.preferences}")

        full_preferences_text = ". ".join(pref_parts)

        source: str = "gemini"
        warnings: List[str] = []
        raw_selections: List[Tuple[Product, int, str]] = []
        summary = ""
        budget_guidance = None

        gemini_result = None
        if self.ai_service.is_available() and candidates:
            try:
                gemini_result = self.ai_service.generate_recommendations(
                    module="party",
                    budget=request.budget,
                    preferences=full_preferences_text,
                    candidates=candidates,
                )
            except Exception as e:
                logger.warning(f"Gemini party recommendation call failed: {e}. Gracefully falling back.")
                gemini_result = None

        if gemini_result and gemini_result.recommendations:
            candidate_map = {p.id: p for p in candidates}
            for rec in gemini_result.recommendations:
                prod = candidate_map.get(rec.product_id)
                if prod is not None:
                    # Enforce guest count scaling if Gemini returned default quantity 1 for bulk items
                    scaled_qty = rec.quantity
                    if rec.quantity == 1 and (
                        "50" in prod.name.lower() or "100" in prod.name.lower()
                    ):
                        scaled_qty, qty_warn = self._determine_guest_scaled_quantity(
                            prod, request.guest_count, budget_dec, Decimal("0.00")
                        )
                        if qty_warn:
                            warnings.append(qty_warn)

                    raw_selections.append((prod, scaled_qty, rec.reason))
                else:
                    # Check if the product exists in the database but belongs to another module
                    other_prod = (
                        db.query(Product)
                        .join(Category, Product.category_id == Category.id)
                        .filter(Product.id == rec.product_id)
                        .first()
                    )
                    if other_prod and other_prod.category and other_prod.category.module_type != "party":
                        warnings.append(
                            f"Omitted product ID {rec.product_id} due to non-party module mismatch ({other_prod.category.module_type})."
                        )
                    else:
                        warnings.append(
                            f"AI-recommended service ID {rec.product_id} was omitted because it was not in the catalog."
                        )

            if raw_selections:
                summary = gemini_result.summary
                budget_guidance = gemini_result.budget_guidance
                if gemini_result.warnings:
                    warnings.extend(gemini_result.warnings)
            else:
                logger.warning("Gemini returned zero valid party service IDs. Triggering fallback.")
                source = "deterministic_fallback"
                raw_selections, fb_warnings = self._generate_party_fallback(db, request, candidates)
                warnings.extend(fb_warnings)
                summary = (
                    f"Rule-based event plan curated for your {request.event_type.replace('_', ' ')} "
                    f"({request.guest_count} guests) within ₹{request.budget:,.2f}."
                )
                budget_guidance = "Prioritize venue and catering before allocating funds for decor and entertainment."
        else:
            source = "deterministic_fallback"
            raw_selections, fb_warnings = self._generate_party_fallback(db, request, candidates)
            warnings.extend(fb_warnings)
            summary = (
                f"Rule-based event plan curated for your {request.event_type.replace('_', ' ')} "
                f"({request.guest_count} guests) within ₹{request.budget:,.2f}."
            )
            budget_guidance = "Prioritize venue and catering before allocating funds for decor and entertainment."

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
            or f"{request.event_type.replace('_', ' ').title()} Party Plan ({request.guest_count} Guests)"
        )

        # -------------------------------------------------------------
        # Database Persistence: BudgetPlan, BudgetItem, Recommendation
        # -------------------------------------------------------------
        plan_record = BudgetPlan(
            user_id=current_user.id,
            title=plan_title,
            module_type="party",
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

        return PartyPlanResponse(
            module="party",
            source=source,
            plan=PartyPlanDetails(
                event_type=request.event_type,
                guest_count=request.guest_count,
                venue_type=request.venue_type,
                food_preference=request.food_preference,
                decoration_preference=request.decoration_preference,
                entertainment_preference=request.entertainment_preference,
                event_duration_hours=request.event_duration_hours,
                estimated_food_budget_per_guest=food_per_guest,
            ),
            category_allocations=category_allocations,
            summary=summary,
            budget_guidance=budget_guidance,
            recommendations=recommended_items,
            budget=budget_summary,
            warnings=warnings,
            plan_id=plan_record.id,
        )


party_planner_service = PartyPlannerService()
