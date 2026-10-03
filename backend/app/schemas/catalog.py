from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CategoryResponse(BaseModel):
    id: int
    name: str
    slug: str
    module_type: str
    description: Optional[str] = None
    icon: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class VendorResponse(BaseModel):
    id: int
    name: str
    platform: str
    description: Optional[str] = None
    rating: float
    website_url: Optional[str] = None
    is_demo: bool

    model_config = ConfigDict(from_attributes=True)


class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    currency: str = "INR"
    currency_symbol: str = "₹"
    category_id: int
    category_name: Optional[str] = None
    module_type: Optional[str] = None
    subcategory: Optional[str] = None
    platform: str
    vendor_id: Optional[int] = None
    vendor_name: Optional[str] = None
    rating: float
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    tags: Optional[str] = None
    style: Optional[str] = None
    availability: bool
    is_demo: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    items: List[ProductResponse]
    total: int
    limit: int
    offset: int
    currency: str = "INR"
    currency_symbol: str = "₹"
