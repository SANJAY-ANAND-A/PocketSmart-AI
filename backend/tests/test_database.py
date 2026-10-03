import pytest
from sqlalchemy import inspect
from app.core.database import SessionLocal, engine, init_db
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.models.vendor import Vendor
from app.models.budget_plan import BudgetPlan, BudgetItem
from app.models.recommendation import Recommendation
from app.services.providers.local_catalog import LocalCatalogProvider


@pytest.fixture(scope="module")
def db_session():
    init_db()
    session = SessionLocal()
    yield session
    session.close()


def test_tables_created():
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    expected_tables = {
        "users",
        "vendors",
        "categories",
        "products",
        "budget_plans",
        "budget_items",
        "recommendations",
    }
    assert expected_tables.issubset(set(table_names)), f"Missing tables: {expected_tables - set(table_names)}"


def test_seeded_vendors(db_session):
    vendors = db_session.query(Vendor).all()
    assert len(vendors) >= 7
    platforms = {v.platform for v in vendors}
    expected_platforms = {"IKEA", "Amazon", "Flipkart", "Swiggy", "Zomato", "OYO", "Local"}
    assert expected_platforms.issubset(platforms)
    for v in vendors:
        assert v.is_demo is True
        assert v.rating >= 4.0


def test_seeded_categories(db_session):
    categories = db_session.query(Category).all()
    assert len(categories) >= 22
    modules = {c.module_type for c in categories}
    assert {"home", "party", "jewelry"} == modules


def test_seeded_products(db_session):
    products = db_session.query(Product).all()
    assert len(products) >= 30
    for p in products:
        assert p.price > 0
        assert p.is_demo is True
        assert p.category_id is not None
        assert p.platform in {"IKEA", "Amazon", "Flipkart", "Swiggy", "Zomato", "OYO", "Local"}


def test_local_catalog_provider(db_session):
    provider = LocalCatalogProvider()
    assert provider.provider_name == "LocalCatalog"
    assert provider.is_live_api is False

    # Search home bed products
    beds = provider.search_products(db=db_session, category_name="Bed", module_type="home")
    assert len(beds) > 0
    for b in beds:
        assert "bed" in b.category.name.lower() or "bed" in (b.subcategory or "").lower()

    # Search party food
    food = provider.search_products(db=db_session, category_name="Food", module_type="party")
    assert len(food) > 0

    # Search jewelry with max price
    affordable_jewelry = provider.search_products(
        db=db_session,
        module_type="jewelry",
        max_price=5000.0,
    )
    assert len(affordable_jewelry) > 0
    for j in affordable_jewelry:
        assert j.price <= 5000.0


def test_model_relationships(db_session):
    # Test BudgetPlan & BudgetItem relationships
    plan = BudgetPlan(
        title="Test Living Room Plan",
        module_type="home",
        total_budget=50000.0,
        allocated_budget=48000.0,
        remaining_budget=2000.0,
        currency="INR",
    )
    db_session.add(plan)
    db_session.flush()

    item = BudgetItem(
        plan_id=plan.id,
        category_name="Sofa",
        allocated_amount=25000.0,
        priority="high",
        reason="Primary seating furniture",
    )
    db_session.add(item)
    db_session.flush()

    product = db_session.query(Product).first()
    rec = Recommendation(
        plan_id=plan.id,
        product_id=product.id,
        match_score=0.92,
        recommendation_reason="Excellent budget fit and high customer rating",
    )
    db_session.add(rec)
    db_session.flush()

    # Query back
    saved_plan = db_session.query(BudgetPlan).filter(BudgetPlan.id == plan.id).first()
    assert saved_plan is not None
    assert len(saved_plan.items) == 1
    assert saved_plan.items[0].category_name == "Sofa"
    assert len(saved_plan.recommendations) == 1
    assert saved_plan.recommendations[0].match_score == 0.92

    # Clean up test plan
    db_session.delete(saved_plan)
    db_session.commit()
