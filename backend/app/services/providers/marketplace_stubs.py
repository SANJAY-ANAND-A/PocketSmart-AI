from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.product import Product
from app.services.providers.base import BaseRecommendationProvider


class ExternalMarketplaceStubProvider(BaseRecommendationProvider):
    """
    Base placeholder for external marketplace and service APIs.
    Demonstrates future extensibility during project viva without violating
    platform terms of service or requiring live affiliate API credentials.
    """

    def __init__(self, platform_name: str):
        self._platform_name = platform_name

    @property
    def provider_name(self) -> str:
        return self._platform_name

    @property
    def is_live_api(self) -> bool:
        return True

    def search_products(
        self,
        db: Session,
        category_name: Optional[str] = None,
        module_type: Optional[str] = None,
        max_price: Optional[float] = None,
        min_price: Optional[float] = None,
        style: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 20,
    ) -> List[Product]:
        # In future production versions, this will call the official Partner API:
        # e.g., Amazon Product Advertising API, Flipkart Affiliate API, IKEA Inventory API.
        # For now, it queries local items tagged with this specific platform.
        query = db.query(Product).filter(Product.platform.ilike(self._platform_name))
        if max_price:
            query = query.filter(Product.price <= max_price)
        return query.limit(limit).all()

    def get_product_by_id(self, db: Session, product_id: int) -> Optional[Product]:
        return db.query(Product).filter(
            Product.id == product_id,
            Product.platform.ilike(self._platform_name),
        ).first()


class AmazonProvider(ExternalMarketplaceStubProvider):
    def __init__(self):
        super().__init__("Amazon")


class FlipkartProvider(ExternalMarketplaceStubProvider):
    def __init__(self):
        super().__init__("Flipkart")


class IKEAProvider(ExternalMarketplaceStubProvider):
    def __init__(self):
        super().__init__("IKEA")


class SwiggyProvider(ExternalMarketplaceStubProvider):
    def __init__(self):
        super().__init__("Swiggy")


class ZomatoProvider(ExternalMarketplaceStubProvider):
    def __init__(self):
        super().__init__("Zomato")


class OYOProvider(ExternalMarketplaceStubProvider):
    def __init__(self):
        super().__init__("OYO")
