from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.category import Category
from app.models.product import Product
from app.models.vendor import Vendor
from app.schemas.catalog import (
    CategoryResponse,
    ProductListResponse,
    ProductResponse,
    VendorResponse,
)

router = APIRouter()


def _format_product_response(p: Product) -> ProductResponse:
    return ProductResponse(
        id=p.id,
        name=p.name,
        description=p.description,
        price=p.price,
        currency=settings.DEFAULT_CURRENCY,
        currency_symbol=settings.CURRENCY_SYMBOL,
        category_id=p.category_id,
        category_name=p.category.name if p.category else None,
        module_type=p.category.module_type if p.category else None,
        subcategory=p.subcategory,
        platform=p.platform,
        vendor_id=p.vendor_id,
        vendor_name=p.vendor.name if p.vendor else None,
        rating=p.rating,
        image_url=p.image_url,
        product_url=p.product_url,
        tags=p.tags,
        style=p.style,
        availability=p.availability,
        is_demo=p.is_demo,
        created_at=p.created_at,
    )


@router.get(
    "/categories",
    response_model=List[CategoryResponse],
    summary="List product and service categories",
    description="Returns available categories, optionally filtered by module (home, party, jewelry) for frontend dropdowns.",
)
def get_categories(
    module: Optional[str] = Query(None, description="Filter categories by module: home, party, or jewelry"),
    db: Session = Depends(get_db),
) -> List[CategoryResponse]:
    query = db.query(Category)
    if module:
        query = query.filter(Category.module_type.ilike(module.strip()))
    return query.order_by(Category.module_type.asc(), Category.name.asc()).all()


@router.get(
    "/vendors",
    response_model=List[VendorResponse],
    summary="List catalog vendors and platforms",
    description="Returns registered vendors and platforms (Amazon, Flipkart, IKEA, Swiggy, Zomato, OYO, Local).",
)
def get_vendors(
    platform: Optional[str] = Query(None, description="Filter by platform name (e.g., IKEA, Amazon, Swiggy)"),
    db: Session = Depends(get_db),
) -> List[VendorResponse]:
    query = db.query(Vendor)
    if platform:
        query = query.filter(Vendor.platform.ilike(f"%{platform.strip()}%"))
    return query.order_by(Vendor.name.asc()).all()


@router.get(
    "",
    response_model=ProductListResponse,
    summary="Search and filter product catalog",
    description="Multi-attribute product search with module, category, vendor, price range, and keyword filtering.",
)
def get_products(
    module: Optional[str] = Query(None, description="Filter by module: home, party, or jewelry"),
    category: Optional[str] = Query(None, description="Filter by category slug, category name, or subcategory"),
    vendor: Optional[str] = Query(None, description="Filter by platform or vendor name"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter in ₹ INR"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter in ₹ INR"),
    search: Optional[str] = Query(None, description="Keyword search across name, description, tags, and style"),
    style: Optional[str] = Query(None, description="Filter by style (e.g. Modern, Minimalist, Traditional, Bohemian)"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return (1-100)"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
) -> ProductListResponse:
    # Build database query with joins
    query = (
        db.query(Product)
        .join(Category, Product.category_id == Category.id)
        .outerjoin(Vendor, Product.vendor_id == Vendor.id)
    )

    # 1. Module filter (home, party, jewelry)
    if module:
        query = query.filter(Category.module_type.ilike(module.strip()))

    # 2. Category / subcategory filter
    if category:
        cat_term = f"%{category.strip()}%"
        query = query.filter(
            or_(
                Category.slug.ilike(cat_term),
                Category.name.ilike(cat_term),
                Product.subcategory.ilike(cat_term),
            )
        )

    # 3. Vendor / Platform filter
    if vendor:
        ven_term = f"%{vendor.strip()}%"
        query = query.filter(
            or_(
                Product.platform.ilike(ven_term),
                Vendor.name.ilike(ven_term),
            )
        )

    # 4. Price range filters
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    # 5. Style filter
    if style:
        query = query.filter(Product.style.ilike(f"%{style.strip()}%"))

    # 6. Keyword search across text fields
    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Product.name.ilike(search_term),
                Product.description.ilike(search_term),
                Product.tags.ilike(search_term),
                Product.subcategory.ilike(search_term),
                Product.style.ilike(search_term),
            )
        )

    # Total matching records count before pagination
    total = query.count()

    # Retrieve paginated items
    products = (
        query.order_by(Product.rating.desc(), Product.id.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return ProductListResponse(
        items=[_format_product_response(p) for p in products],
        total=total,
        limit=limit,
        offset=offset,
        currency=settings.DEFAULT_CURRENCY,
        currency_symbol=settings.CURRENCY_SYMBOL,
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get single product by ID",
    description="Returns complete details for a single catalog product or service item. Returns 404 if not found.",
)
def get_product_by_id(
    product_id: int,
    db: Session = Depends(get_db),
) -> ProductResponse:
    product = (
        db.query(Product)
        .join(Category, Product.category_id == Category.id)
        .outerjoin(Vendor, Product.vendor_id == Vendor.id)
        .filter(Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} was not found in the catalog.",
        )

    return _format_product_response(product)
