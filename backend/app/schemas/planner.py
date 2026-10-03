from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class BudgetItemInput(BaseModel):
    product_id: int = Field(..., gt=0, description="Product catalog ID")
    quantity: int = Field(1, gt=0, le=1000, description="Quantity required (positive integer)")


class BudgetPlanRequest(BaseModel):
    module: Literal["home", "party", "jewelry"] = Field(
        ...,
        description="Target module: 'home' (Interior), 'party' (Event), or 'jewelry'",
    )
    total_budget: float = Field(
        ...,
        gt=0,
        description="Total allocated budget in INR (₹), must be positive",
    )
    items: List[BudgetItemInput] = Field(
        ...,
        min_length=1,
        description="List of selected catalog items and their quantities",
    )
    title: Optional[str] = Field(
        None,
        max_length=200,
        description="Optional custom title for the budget plan",
    )
    save_plan: bool = Field(
        False,
        description="Set to true to persist this plan into the database for the user",
    )


class CalculatedItemDetail(BaseModel):
    product_id: int
    name: str
    unit_price: float
    quantity: int
    subtotal: float
    category_name: Optional[str] = None
    module_type: str
    platform: str
    is_demo: bool = True

    model_config = ConfigDict(from_attributes=True)


class BudgetPlanResponse(BaseModel):
    module: str
    total_budget: float
    total_cost: float
    remaining_budget: float
    over_budget_amount: float
    utilization_percentage: float
    is_within_budget: bool
    currency: str = "INR"
    currency_symbol: str = "₹"
    items: List[CalculatedItemDetail]
    plan_id: Optional[int] = None
    title: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
