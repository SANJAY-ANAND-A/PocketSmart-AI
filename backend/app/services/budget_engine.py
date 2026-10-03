from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Tuple


class BudgetEngine:
    """
    Deterministic Financial and Budget Calculation Engine for PocketSmart AI.
    Guarantees strict mathematical accuracy using Decimals.
    Gemini/LLMs never perform raw budget arithmetic.
    """

    TWO_PLACES = Decimal("0.01")

    @classmethod
    def to_decimal(cls, value: float | int | str | Decimal) -> Decimal:
        """Converts float or numeric value to Decimal safely."""
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value)).quantize(cls.TWO_PLACES, rounding=ROUND_HALF_UP)

    @classmethod
    def calculate_subtotal(cls, unit_price: Decimal, quantity: int) -> Decimal:
        """Calculate line-item subtotal (unit_price * quantity)."""
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")
        if unit_price < Decimal("0"):
            raise ValueError("Unit price cannot be negative.")
        return (unit_price * quantity).quantize(cls.TWO_PLACES, rounding=ROUND_HALF_UP)

    @classmethod
    def calculate_total_cost(cls, subtotals: List[Decimal]) -> Decimal:
        """Sum all item subtotals deterministically."""
        total = sum(subtotals, Decimal("0.00"))
        return total.quantize(cls.TWO_PLACES, rounding=ROUND_HALF_UP)

    @classmethod
    def calculate_remaining_budget(cls, total_budget: Decimal, total_cost: Decimal) -> Decimal:
        """
        Calculate remaining budget.
        Returns budget - cost if within budget; returns 0.00 if over budget.
        """
        if total_cost > total_budget:
            return Decimal("0.00")
        return (total_budget - total_cost).quantize(cls.TWO_PLACES, rounding=ROUND_HALF_UP)

    @classmethod
    def calculate_over_budget_amount(cls, total_budget: Decimal, total_cost: Decimal) -> Decimal:
        """
        Calculate over-budget deficit.
        Returns cost - budget if over budget; returns 0.00 if within budget.
        """
        if total_cost <= total_budget:
            return Decimal("0.00")
        return (total_cost - total_budget).quantize(cls.TWO_PLACES, rounding=ROUND_HALF_UP)

    @classmethod
    def calculate_utilization_percentage(cls, total_budget: Decimal, total_cost: Decimal) -> float:
        """
        Calculate percentage of budget utilized: (total_cost / total_budget) * 100.
        Rounded to 2 decimal places.
        """
        if total_budget <= Decimal("0"):
            raise ValueError("Total budget must be strictly positive.")
        utilization = (total_cost / total_budget) * Decimal("100")
        return float(utilization.quantize(cls.TWO_PLACES, rounding=ROUND_HALF_UP))

    @classmethod
    def is_within_budget(cls, total_budget: Decimal, total_cost: Decimal) -> bool:
        """Boolean check whether planned cost is within or equal to total budget."""
        return total_cost <= total_budget
