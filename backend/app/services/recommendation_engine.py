import logging
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload
from app.core.config import settings
from app.models.budget_plan import BudgetItem, BudgetPlan
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.schemas.catalog import ProductResponse
from app.schemas.recommendation import (
    BudgetSummary,
    GeminiStructuredResponse,
    RecommendationRequest,
    RecommendationResponse,
    RecommendedItemDetail,
)
from app.services.budget_engine import BudgetEngine
from app.services.gemini_service import GeminiService, gemini_service

logger = logging.getLogger(__name__)


def _format_product_response(p: Product) -> ProductResponse:
    category_name = None
    module_type = None
    try:
        if getattr(p, "category", None) is not None:
            category_name = p.category.name
            module_type = p.category.module_type
    except Exception:
        pass
    if not module_type and hasattr(p, "category_id"):
        module_type = "home"

    vendor_name = None
    try:
        if getattr(p, "vendor", None) is not None:
            vendor_name = p.vendor.name
    except Exception:
        pass

    return ProductResponse(
        id=p.id,
        name=p.name,
        description=p.description,
        price=p.price,
        currency=settings.DEFAULT_CURRENCY,
        currency_symbol=settings.CURRENCY_SYMBOL,
        category_id=p.category_id,
        category_name=category_name,
        module_type=module_type,
        subcategory=p.subcategory,
        platform=p.platform,
        vendor_id=p.vendor_id,
        vendor_name=vendor_name,
        rating=p.rating,
        image_url=p.image_url,
        product_url=p.product_url,
        tags=p.tags,
        style=p.style,
        availability=p.availability,
        is_demo=p.is_demo,
        created_at=p.created_at,
    )


class RecommendationEngine:
    """
    Recommendation Orchestration Engine for PocketSmart AI.
    Coordinates between Google Gemini AI, candidate catalog retrieval,
    strict schema validation, deterministic fallback, and budget safety enforcement.
    """

    def __init__(self, ai_service: Optional[GeminiService] = None):
        self.ai_service = ai_service if ai_service is not None else gemini_service

    def get_candidate_products(self, db: Session, module: str, limit: int = 25) -> List[Product]:
        """Fetch available catalog candidate products for the given module domain."""
        return (
            db.query(Product)
            .options(joinedload(Product.category), joinedload(Product.vendor))
            .join(Category, Product.category_id == Category.id)
            .filter(
                Category.module_type.ilike(module.strip()),
                Product.availability == True,
            )
            .order_by(Product.rating.desc(), Product.price.asc())
            .limit(limit)
            .all()
        )

    def _score_product_relevance(self, product: Product, keywords: List[str]) -> float:
        """Calculates a deterministic keyword relevance score for fallback sorting."""
        searchable_text = f"{product.name} {product.description or ''} {product.tags or ''} {product.style or ''} {product.subcategory or ''}".lower()
        score = product.rating  # Base score between 4.0 and 5.0
        for kw in keywords:
            if kw and len(kw) > 2 and kw in searchable_text:
                score += 3.0
        return score

    def generate_deterministic_fallback(
        self,
        db: Session,
        module: str,
        budget: float,
        preferences: str,
        candidates: List[Product],
    ) -> Tuple[List[Tuple[Product, int, str]], List[str]]:
        """
        Deterministic rule-based recommendation fallback.
        Selects top-rated, diverse products matching user preference keywords within budget.
        """
        keywords = [w.strip().lower() for w in preferences.replace(",", " ").replace(".", " ").split() if len(w) > 2]
        scored_candidates = sorted(
            candidates,
            key=lambda p: self._score_product_relevance(p, keywords),
            reverse=True,
        )

        selected: List[Tuple[Product, int, str]] = []
        current_cost = Decimal("0.00")
        budget_dec = BudgetEngine.to_decimal(budget)
        used_categories = set()

        for prod in scored_candidates:
            cat_id = prod.category_id
            prod_price_dec = BudgetEngine.to_decimal(prod.price)

            # Prioritize one product per category first for diversity
            if cat_id not in used_categories or len(selected) < 2:
                if current_cost + prod_price_dec <= budget_dec:
                    selected.append((
                        prod,
                        1,
                        f"Selected based on high rating ({prod.rating}★) and match with '{prod.style or 'essential'}' preferences.",
                    ))
                    current_cost += prod_price_dec
                    used_categories.add(cat_id)

            if len(selected) >= 4:
                break

        # If no items were affordable, pick at least the most affordable single candidate
        if not selected and scored_candidates:
            cheapest = min(scored_candidates, key=lambda p: p.price)
            selected.append((
                cheapest,
                1,
                f"Selected as the most accessible option in the {module} catalog.",
            ))

        warnings = ["AI recommendations are temporarily unavailable. Showing rule-based recommendations."]
        return selected, warnings

    def process_recommendation_request(
        self,
        db: Session,
        request: RecommendationRequest,
        current_user: User,
    ) -> RecommendationResponse:
        """
        Main pipeline:
        1. Fetch candidates from DB
        2. Attempt Gemini AI structured recommendation
        3. If Gemini fails/unavailable -> run deterministic fallback
        4. Validate product IDs & prices against SQLite
        5. Enforce deterministic budget safety
        6. Persist plan if requested
        """
        candidates = self.get_candidate_products(db, request.module)
        gemini_result: Optional[GeminiStructuredResponse] = None

        if self.ai_service.is_available() and candidates:
            gemini_result = self.ai_service.generate_recommendations(
                module=request.module,
                budget=request.budget,
                preferences=request.preferences,
                candidates=candidates,
            )

        source: str = "gemini"
        warnings: List[str] = []
        raw_selections: List[Tuple[Product, int, str]] = []
        summary = ""
        budget_guidance = None

        if gemini_result and gemini_result.recommendations:
            # Map candidate products by ID
            candidate_map = {p.id: p for p in candidates}
            for rec in gemini_result.recommendations:
                prod = candidate_map.get(rec.product_id)
                if prod is not None:
                    raw_selections.append((prod, rec.quantity, rec.reason))
                else:
                    warnings.append(f"AI-recommended product ID {rec.product_id} was omitted because it was not in the catalog.")

            if raw_selections:
                summary = gemini_result.summary
                budget_guidance = gemini_result.budget_guidance
                if gemini_result.warnings:
                    warnings.extend(gemini_result.warnings)
            else:
                # If Gemini returned only non-existent product IDs, fallback
                logger.warning("Gemini returned zero valid catalog product IDs. Triggering fallback.")
                source = "deterministic_fallback"
                raw_selections, fb_warnings = self.generate_deterministic_fallback(
                    db, request.module, request.budget, request.preferences, candidates
                )
                warnings.extend(fb_warnings)
                summary = f"Rule-based plan curated for your {request.module} requirements within ₹{request.budget:,.2f}."
                budget_guidance = "Review each item's allocation to ensure it covers your key priorities."
        else:
            source = "deterministic_fallback"
            raw_selections, fb_warnings = self.generate_deterministic_fallback(
                db, request.module, request.budget, request.preferences, candidates
            )
            warnings.extend(fb_warnings)
            summary = f"Rule-based plan curated for your {request.module} requirements within ₹{request.budget:,.2f}."
            budget_guidance = "Review each item's allocation to ensure it covers your key priorities."

        # -------------------------------------------------------------
        # Deterministic Budget Safety & Dynamic Adjustment
        # -------------------------------------------------------------
        # Calculate subtotal using authoritative DB prices
        budget_dec = BudgetEngine.to_decimal(request.budget)
        adjusted_selections: List[Tuple[Product, int, str]] = list(raw_selections)

        # Check total cost
        def calc_total(items: List[Tuple[Product, int, str]]) -> Decimal:
            subtotals = [
                BudgetEngine.calculate_subtotal(BudgetEngine.to_decimal(p.price), qty)
                for p, qty, _ in items
            ]
            return BudgetEngine.calculate_total_cost(subtotals)

        total_cost_dec = calc_total(adjusted_selections)

        # If recommendations exceed budget, deterministically trim items
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

        # Build final recommended items
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

        plan_id = None
        if request.save_plan:
            title = request.title or f"{request.module.capitalize()} AI Budget Plan"
            plan = BudgetPlan(
                user_id=current_user.id,
                title=title,
                module_type=request.module,
                total_budget=float(budget_dec),
                allocated_budget=float(final_total_cost),
                remaining_budget=float(remaining_budget),
                currency=settings.DEFAULT_CURRENCY,
                ai_reasoning=summary,
                is_fallback=(source == "deterministic_fallback"),
            )
            db.add(plan)
            db.flush()

            for item_detail in recommended_items:
                budget_item = BudgetItem(
                    plan_id=plan.id,
                    category_name=item_detail.product.category_name or "General",
                    allocated_amount=item_detail.subtotal,
                    spent_amount=item_detail.subtotal,
                    priority="high",
                    reason=item_detail.reason,
                )
                db.add(budget_item)

            db.commit()
            db.refresh(plan)
            plan_id = plan.id

        return RecommendationResponse(
            source=source,
            module=request.module,
            summary=summary,
            budget_guidance=budget_guidance,
            recommendations=recommended_items,
            budget=budget_summary,
            warnings=warnings,
            plan_id=plan_id,
        )


recommendation_engine = RecommendationEngine()
