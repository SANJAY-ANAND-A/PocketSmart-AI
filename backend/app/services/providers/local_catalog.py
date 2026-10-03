from typing import Any, Dict, List, Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.models.category import Category
from app.models.product import Product
from app.services.providers.base import BaseRecommendationProvider


class LocalCatalogProvider(BaseRecommendationProvider):
    """
    Local catalog provider that queries the local SQLite/PostgreSQL database.
    This serves as the primary data source for the MVP college project.
    """

    @property
    def provider_name(self) -> str:
        return "LocalCatalog"

    @property
    def is_live_api(self) -> bool:
        return False

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
        query = db.query(Product).join(Category, Product.category_id == Category.id)

        # Filter by module (home, party, jewelry)
        if module_type:
            query = query.filter(Category.module_type.ilike(module_type))

        # Filter by category name
        if category_name:
            query = query.filter(
                or_(
                    Category.name.ilike(f"%{category_name}%"),
                    Product.subcategory.ilike(f"%{category_name}%"),
                )
            )

        # Price range filter
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        if max_price is not None:
            query = query.filter(Product.price <= max_price)

        # Style filter (if requested)
        if style:
            query = query.filter(Product.style.ilike(f"%{style}%"))

        # Limit and order by rating descending
        products = query.filter(Product.availability == True).order_by(Product.rating.desc()).limit(limit).all()

        # Tag-based filtering if tags are supplied
        if tags:
            tag_lower = [t.lower() for t in tags]
            filtered = []
            for p in products:
                product_tags = (p.tags or "").lower()
                if any(t in product_tags for t in tag_lower):
                    filtered.append(p)
            if filtered:
                return filtered

        return products

    def get_product_by_id(self, db: Session, product_id: int) -> Optional[Product]:
        return db.query(Product).filter(Product.id == product_id).first()
