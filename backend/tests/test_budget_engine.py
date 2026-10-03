from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from app.core.database import SessionLocal, init_db
from app.main import app
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.seed import seed_database
from app.services.budget_engine import BudgetEngine

client = TestClient(app)

TEST_USER_EMAIL = "budget_tester@example.com"
TEST_USER_USERNAME = "budget_tester"
TEST_USER_PASSWORD = "TestBudgetPass123"


@pytest.fixture(scope="module", autouse=True)
def setup_test_environment():
    init_db()
    seed_database()

    # Ensure test user exists
    db = SessionLocal()
    user = db.query(User).filter(User.username == TEST_USER_USERNAME).first()
    if not user:
        from app.core.security import get_password_hash
        user = User(
            email=TEST_USER_EMAIL,
            username=TEST_USER_USERNAME,
            hashed_password=get_password_hash(TEST_USER_PASSWORD),
            full_name="Budget Test Engineer",
            is_active=True,
        )
        db.add(user)
        db.commit()
    db.close()


def get_auth_token():
    login_res = client.post(
        "/api/auth/login",
        json={"username_or_email": TEST_USER_USERNAME, "password": TEST_USER_PASSWORD},
    )
    assert login_res.status_code == 200
    return login_res.json()["access_token"]


# =========================================================================
# 1. BudgetEngine Unit Tests (Pure Deterministic Arithmetic with Decimal)
# =========================================================================

def test_engine_subtotal_calculation():
    unit_price = Decimal("14999.50")
    quantity = 3
    subtotal = BudgetEngine.calculate_subtotal(unit_price, quantity)
    assert subtotal == Decimal("44998.50")


def test_engine_negative_subtotal_or_quantity_rejection():
    with pytest.raises(ValueError, match="Quantity must be greater than zero"):
        BudgetEngine.calculate_subtotal(Decimal("100.00"), 0)

    with pytest.raises(ValueError, match="Quantity must be greater than zero"):
        BudgetEngine.calculate_subtotal(Decimal("100.00"), -2)

    with pytest.raises(ValueError, match="Unit price cannot be negative"):
        BudgetEngine.calculate_subtotal(Decimal("-50.00"), 1)


def test_engine_total_cost_calculation():
    subtotals = [Decimal("1000.25"), Decimal("2500.50"), Decimal("1499.25")]
    total = BudgetEngine.calculate_total_cost(subtotals)
    assert total == Decimal("5000.00")


def test_engine_remaining_and_over_budget_within():
    budget = Decimal("10000.00")
    cost = Decimal("7500.00")
    assert BudgetEngine.is_within_budget(budget, cost) is True
    assert BudgetEngine.calculate_remaining_budget(budget, cost) == Decimal("2500.00")
    assert BudgetEngine.calculate_over_budget_amount(budget, cost) == Decimal("0.00")
    assert BudgetEngine.calculate_utilization_percentage(budget, cost) == 75.00


def test_engine_remaining_and_over_budget_exceeded():
    budget = Decimal("10000.00")
    cost = Decimal("12500.00")
    assert BudgetEngine.is_within_budget(budget, cost) is False
    assert BudgetEngine.calculate_remaining_budget(budget, cost) == Decimal("0.00")
    assert BudgetEngine.calculate_over_budget_amount(budget, cost) == Decimal("2500.00")
    assert BudgetEngine.calculate_utilization_percentage(budget, cost) == 125.00


# =========================================================================
# 2. Budget Planner API Endpoint Integration Tests
# =========================================================================

def test_planner_basic_budget_calculation_within_budget():
    token = get_auth_token()
    db = SessionLocal()
    # Pick a Home bed product
    bed = (
        db.query(Product)
        .join(Category, Product.category_id == Category.id)
        .filter(Category.module_type == "home")
        .first()
    )
    db.close()
    assert bed is not None

    total_budget = bed.price + 5000.0

    response = client.post(
        "/api/planner/budget",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "module": "home",
            "total_budget": total_budget,
            "items": [{"product_id": bed.id, "quantity": 1}],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["module"] == "home"
    assert data["total_budget"] == total_budget
    assert data["total_cost"] == bed.price
    assert data["remaining_budget"] == 5000.0
    assert data["over_budget_amount"] == 0.0
    assert data["is_within_budget"] is True
    assert data["currency"] == "INR"
    assert data["currency_symbol"] == "₹"
    assert len(data["items"]) == 1
    assert data["items"][0]["subtotal"] == bed.price


def test_planner_multiple_products_and_quantities():
    token = get_auth_token()
    db = SessionLocal()
    home_prods = (
        db.query(Product)
        .join(Category, Product.category_id == Category.id)
        .filter(Category.module_type == "home")
        .limit(2)
        .all()
    )
    db.close()
    assert len(home_prods) >= 2

    p1, p2 = home_prods[0], home_prods[1]
    expected_cost = (p1.price * 2) + (p2.price * 1)
    total_budget = expected_cost + 10000.0

    response = client.post(
        "/api/planner/budget",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "module": "home",
            "total_budget": total_budget,
            "items": [
                {"product_id": p1.id, "quantity": 2},
                {"product_id": p2.id, "quantity": 1},
            ],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_cost"] == expected_cost
    assert data["remaining_budget"] == 10000.0
    assert len(data["items"]) == 2


def test_planner_over_budget_plan():
    token = get_auth_token()
    db = SessionLocal()
    bed = (
        db.query(Product)
        .join(Category, Product.category_id == Category.id)
        .filter(Category.module_type == "home")
        .first()
    )
    db.close()

    tight_budget = bed.price - 2000.0
    assert tight_budget > 0

    response = client.post(
        "/api/planner/budget",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "module": "home",
            "total_budget": tight_budget,
            "items": [{"product_id": bed.id, "quantity": 1}],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_within_budget"] is False
    assert data["over_budget_amount"] == 2000.0
    assert data["remaining_budget"] == 0.0
    assert data["utilization_percentage"] > 100.0


def test_planner_duplicate_product_handling():
    token = get_auth_token()
    db = SessionLocal()
    prod = (
        db.query(Product)
        .join(Category, Product.category_id == Category.id)
        .filter(Category.module_type == "jewelry")
        .first()
    )
    db.close()

    # Pass the same product twice (qty 2 and qty 3 -> should aggregate to qty 5)
    response = client.post(
        "/api/planner/budget",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "module": "jewelry",
            "total_budget": (prod.price * 5) + 1000.0,
            "items": [
                {"product_id": prod.id, "quantity": 2},
                {"product_id": prod.id, "quantity": 3},
            ],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 5
    assert data["items"][0]["subtotal"] == prod.price * 5


def test_planner_module_mismatch_rejection():
    token = get_auth_token()
    db = SessionLocal()
    party_item = (
        db.query(Product)
        .join(Category, Product.category_id == Category.id)
        .filter(Category.module_type == "party")
        .first()
    )
    db.close()

    # Attempt to add a party product to a 'home' budget plan
    response = client.post(
        "/api/planner/budget",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "module": "home",
            "total_budget": 50000.0,
            "items": [{"product_id": party_item.id, "quantity": 1}],
        },
    )

    assert response.status_code == 400
    assert "module mismatch" in response.json()["detail"].lower()


def test_planner_nonexistent_product_returns_404():
    token = get_auth_token()
    response = client.post(
        "/api/planner/budget",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "module": "home",
            "total_budget": 50000.0,
            "items": [{"product_id": 999999, "quantity": 1}],
        },
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_planner_zero_or_negative_budget_rejection():
    token = get_auth_token()
    # Zero budget
    r0 = client.post(
        "/api/planner/budget",
        headers={"Authorization": f"Bearer {token}"},
        json={"module": "home", "total_budget": 0, "items": [{"product_id": 1, "quantity": 1}]},
    )
    assert r0.status_code == 422

    # Negative budget
    r_neg = client.post(
        "/api/planner/budget",
        headers={"Authorization": f"Bearer {token}"},
        json={"module": "home", "total_budget": -500, "items": [{"product_id": 1, "quantity": 1}]},
    )
    assert r_neg.status_code == 422


def test_planner_zero_or_negative_quantity_rejection():
    token = get_auth_token()
    # Zero quantity
    r0 = client.post(
        "/api/planner/budget",
        headers={"Authorization": f"Bearer {token}"},
        json={"module": "home", "total_budget": 10000, "items": [{"product_id": 1, "quantity": 0}]},
    )
    assert r0.status_code == 422

    # Negative quantity
    r_neg = client.post(
        "/api/planner/budget",
        headers={"Authorization": f"Bearer {token}"},
        json={"module": "home", "total_budget": 10000, "items": [{"product_id": 1, "quantity": -2}]},
    )
    assert r_neg.status_code == 422


def test_planner_empty_items_rejection():
    token = get_auth_token()
    response = client.post(
        "/api/planner/budget",
        headers={"Authorization": f"Bearer {token}"},
        json={"module": "home", "total_budget": 50000, "items": []},
    )
    assert response.status_code == 422


def test_planner_invalid_module_rejection():
    token = get_auth_token()
    response = client.post(
        "/api/planner/budget",
        headers={"Authorization": f"Bearer {token}"},
        json={"module": "automotive", "total_budget": 50000, "items": [{"product_id": 1, "quantity": 1}]},
    )
    assert response.status_code == 422


def test_planner_unauthenticated_access_rejected():
    response = client.post(
        "/api/planner/budget",
        json={"module": "home", "total_budget": 50000, "items": [{"product_id": 1, "quantity": 1}]},
    )
    assert response.status_code == 401


def test_planner_save_plan_persistence():
    token = get_auth_token()
    db = SessionLocal()
    prod = (
        db.query(Product)
        .join(Category, Product.category_id == Category.id)
        .filter(Category.module_type == "party")
        .first()
    )
    db.close()

    response = client.post(
        "/api/planner/budget",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "module": "party",
            "total_budget": prod.price + 2000.0,
            "items": [{"product_id": prod.id, "quantity": 1}],
            "title": "College Annual Fest Stage Budget",
            "save_plan": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["plan_id"] is not None
    assert data["title"] == "College Annual Fest Stage Budget"

    # Verify saved in SQLite database
    db = SessionLocal()
    from app.models.budget_plan import BudgetPlan
    saved_plan = db.query(BudgetPlan).filter(BudgetPlan.id == data["plan_id"]).first()
    assert saved_plan is not None
    assert saved_plan.title == "College Annual Fest Stage Budget"
    assert saved_plan.module_type == "party"
    assert len(saved_plan.items) == 1
    db.close()
