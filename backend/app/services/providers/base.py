from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.product import Product


class BaseRecommendationProvider(ABC):
    """
    Abstract base class for product and service recommendation providers.
    Follows the Provider/Adapter design pattern to decouple catalog sources
    (Local SQLite catalog vs future external APIs like Amazon, Flipkart, IKEA).
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider / platform."""
        pass

    @property
    @abstractmethod
    def is_live_api(self) -> bool:
        """Indicates whether this provider connects to a live marketplace API or local catalog."""
        pass

    @abstractmethod
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
        """Search products matching specified criteria."""
        pass

    @abstractmethod
    def get_product_by_id(self, db: Session, product_id: int) -> Optional[Product]:
        """Retrieve a single product by its unique identifier."""
        pass
