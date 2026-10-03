from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from app.core.database import SessionLocal, init_db
from app.main import app
from app.models.budget_plan import BudgetItem, BudgetPlan
from app.models.category import Category
from app.models.product import Product
from app.models.recommendation import Recommendation
from app.models.user import User
from app.schemas.recommendation import GeminiProductRec, GeminiStructuredResponse
from app.seed import seed_database
from app.services.home_planner_service import home_planner_service

client = TestClient(app)

TEST_USER_EMAIL = "home_planner_user@example.com"
TEST_USER_USERNAME = "home_planner_user"
TEST_USER_PASSWORD = "HomePassword123"


@pytest.fixture(scope="module", autouse=True)
def setup_environment():
    init_db()
    seed_database()

    db = SessionLocal()
    user = db.query(User).filter(User.username == TEST_USER_USERNAME).first()
    if not user:
        from app.core.security import get_password_hash
        user = User(
            email=TEST_USER_EMAIL,
            username=TEST_USER_USERNAME,
            hashed_password=get_password_hash(TEST_USER_PASSWORD),
            full_name="Home Planner Test User",
            is_active=True,
        )
        db.add(user)
        db.commit()
    db.close()


def get_auth_token():
    res = client.post(
        "/api/auth/login",
        json={"username_or_email": TEST_USER_USERNAME, "password": TEST_USER_PASSWORD},
    )
    assert res.status_code == 200
    return res.json()["access_token"]


# =========================================================================
# Home Interior Planner Tests
# =========================================================================

def test_home_planner_unauthenticated_rejected():
    response = client.post(
        "/api/planner/home",
        json={
            "budget": 80000.0,
            "room_type": "bedroom",
            "style": "Modern Minimalist",
        },
    )
    assert response.status_code == 401


def test_home_planner_invalid_budget():
    token = get_auth_token()
    # Negative budget
    res_neg = client.post(
        "/api/planner/home",
        headers={"Authorization": f"Bearer {token}"},
        json={"budget": -5000.0, "room_type": "bedroom"},
    )
    assert res_neg.status_code == 422

    # Zero budget
    res_zero = client.post(
        "/api/planner/home",
        headers={"Authorization": f"Bearer {token}"},
        json={"budget": 0.0, "room_type": "bedroom"},
    )
    assert res_zero.status_code == 422


def test_home_planner_invalid_room_type():
    token = get_auth_token()
    response = client.post(
        "/api/planner/home",
        headers={"Authorization": f"Bearer {token}"},
        json={"budget": 50000.0, "room_type": "garage_attic_warehouse"},
    )
    assert response.status_code == 422


def test_home_planner_valid_bedroom_request():
    token = get_auth_token()
    with patch.object(home_planner_service.ai_service, "is_available", return_value=False):
        response = client.post(
            "/api/planner/home",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "budget": 60000.0,
                "room_type": "bedroom",
                "style": "Scandinavian",
                "color_preferences": ["white", "beige", "oak"],
                "priorities": ["bed", "wardrobe"],
                "required_items": ["queen storage bed", "3-door wardrobe"],
                "preferences": "A peaceful Scandinavian master bedroom with soft natural textures.",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["module"] == "home"
    assert data["plan"]["room_type"] == "bedroom"
    assert data["plan"]["style"] == "Scandinavian"
    assert len(data["recommendations"]) > 0
    assert data["budget"]["total_budget"] == 60000.0
    assert data["budget"]["is_within_budget"] is True
    assert data["budget"]["currency"] == "INR"
    assert data["budget"]["currency_symbol"] == "₹"


def test_home_planner_valid_living_room_request():
    token = get_auth_token()
    with patch.object(home_planner_service.ai_service, "is_available", return_value=False):
        response = client.post(
            "/api/planner/home",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "budget": 50000.0,
                "room_type": "living_room",
                "style": "Modern",
                "color_preferences": ["grey", "brass", "teal"],
                "priorities": ["sofa", "lighting"],
                "preferences": "Cozy living room with ambient lighting for movie nights.",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["plan"]["room_type"] == "living_room"
    assert len(data["recommendations"]) > 0
    assert data["budget"]["is_within_budget"] is True


def test_home_planner_home_only_catalog_filtering():
    """Verify that candidates retrieved for the home planner only come from the 'home' module."""
    db = SessionLocal()
    candidates = home_planner_service.get_home_candidates(db, room_type="bedroom")
    db.close()

    assert len(candidates) > 0
    for prod in candidates:
        assert prod.category.module_type == "home"


def test_home_planner_gemini_success_flow():
    token = get_auth_token()
    db = SessionLocal()
    home_beds = (
        db.query(Product)
        .join(Category, Product.category_id == Category.id)
        .filter(Category.module_type == "home", Category.name == "Bed")
        .all()
    )
    db.close()
    assert len(home_beds) >= 1

    mock_gemini_output = GeminiStructuredResponse(
        module="home",
        summary="A serene Japanese-Scandinavian minimalist master suite.",
        budget_guidance="Focus on ergonomic sleep foundation.",
        recommendations=[
            GeminiProductRec(
                product_id=home_beds[0].id,
                quantity=1,
                reason="Primary focal piece offering clean lines and hidden hydraulic storage.",
            )
        ],
    )

    with patch.object(home_planner_service.ai_service, "is_available", return_value=True):
        with patch.object(home_planner_service.ai_service, "generate_recommendations", return_value=mock_gemini_output):
            response = client.post(
                "/api/planner/home",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "budget": 80000.0,
                    "room_type": "bedroom",
                    "style": "Minimalist",
                    "color_preferences": ["white", "oak"],
                    "priorities": ["bed"],
                    "required_items": ["queen bed"],
                    "preferences": "Minimalist room setup.",
                },
            )

    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "gemini"
    assert data["module"] == "home"
    assert len(data["recommendations"]) == 1
    assert data["recommendations"][0]["product"]["id"] == home_beds[0].id
    assert data["budget"]["is_within_budget"] is True
    assert data["plan_id"] is not None


def test_home_planner_gemini_unavailable_fallback():
    token = get_auth_token()
    with patch.object(home_planner_service.ai_service, "is_available", return_value=False):
        response = client.post(
            "/api/planner/home",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "budget": 75000.0,
                "room_type": "bedroom",
                "style": "Scandinavian",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "deterministic_fallback"
    assert any("rule-based" in w.lower() for w in data["warnings"])
    assert data["budget"]["is_within_budget"] is True


def test_home_planner_party_or_jewelry_product_rejection():
    """Verify that if Gemini hallucinates a party or jewelry product ID, it is omitted from the home plan."""
    token = get_auth_token()
    db = SessionLocal()
    party_item = (
        db.query(Product)
        .join(Category, Product.category_id == Category.id)
        .filter(Category.module_type == "party")
        .first()
    )
    home_item = (
        db.query(Product)
        .join(Category, Product.category_id == Category.id)
        .filter(Category.module_type == "home")
        .first()
    )
    db.close()

    mock_gemini_output = GeminiStructuredResponse(
        module="home",
        summary="Mixed recommendations test.",
        recommendations=[
            GeminiProductRec(product_id=home_item.id, quantity=1, reason="Valid home bed"),
            GeminiProductRec(product_id=party_item.id, quantity=1, reason="Invalid party catering in bedroom"),
        ],
    )

    with patch.object(home_planner_service.ai_service, "is_available", return_value=True):
        with patch.object(home_planner_service.ai_service, "generate_recommendations", return_value=mock_gemini_output):
            response = client.post(
                "/api/planner/home",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "budget": 60000.0,
                    "room_type": "bedroom",
                },
            )

    assert response.status_code == 200
    data = response.json()
    rec_ids = [r["product"]["id"] for r in data["recommendations"]]
    assert home_item.id in rec_ids
    assert party_item.id not in rec_ids  # Party item must NOT enter home plan
    assert any("non-home" in w.lower() for w in data["warnings"])


def test_home_planner_invalid_product_id():
    token = get_auth_token()
    db = SessionLocal()
    home_item = (
        db.query(Product)
        .join(Category, Product.category_id == Category.id)
        .filter(Category.module_type == "home")
        .first()
    )
    db.close()

    mock_gemini_output = GeminiStructuredResponse(
        module="home",
        summary="Testing invalid ID.",
        recommendations=[
            GeminiProductRec(product_id=home_item.id, quantity=1, reason="Legitimate furniture"),
            GeminiProductRec(product_id=888888, quantity=1, reason="Fake hallucinated ID"),
        ],
    )

    with patch.object(home_planner_service.ai_service, "is_available", return_value=True):
        with patch.object(home_planner_service.ai_service, "generate_recommendations", return_value=mock_gemini_output):
            response = client.post(
                "/api/planner/home",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "budget": 60000.0,
                    "room_type": "bedroom",
                },
            )

    assert response.status_code == 200
    data = response.json()
    rec_ids = [r["product"]["id"] for r in data["recommendations"]]
    assert 888888 not in rec_ids
    assert home_item.id in rec_ids


def test_home_planner_over_budget_adjustment():
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

    # Budget is smaller than sum of both items
    tight_budget = min(home_prods[0].price, home_prods[1].price) + 2000.0

    mock_gemini_output = GeminiStructuredResponse(
        module="home",
        summary="High budget plan.",
        recommendations=[
            GeminiProductRec(product_id=home_prods[0].id, quantity=1, reason="Furniture 1"),
            GeminiProductRec(product_id=home_prods[1].id, quantity=1, reason="Furniture 2"),
        ],
    )

    with patch.object(home_planner_service.ai_service, "is_available", return_value=True):
        with patch.object(home_planner_service.ai_service, "generate_recommendations", return_value=mock_gemini_output):
            response = client.post(
                "/api/planner/home",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "budget": tight_budget,
                    "room_type": "bedroom",
                },
            )

    assert response.status_code == 200
    data = response.json()
    assert data["budget"]["total_cost"] <= tight_budget
    assert data["budget"]["is_within_budget"] is True
    assert any("trimmed" in w.lower() for w in data["warnings"])


def test_home_planner_database_persistence():
    token = get_auth_token()
    with patch.object(home_planner_service.ai_service, "is_available", return_value=False):
        response = client.post(
            "/api/planner/home",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "budget": 70000.0,
                "room_type": "bedroom",
                "style": "Bohemian",
                "title": "Master Bohemian Suite",
            },
        )

    assert response.status_code == 200
    data = response.json()
    plan_id = data["plan_id"]
    assert plan_id is not None

    # Query database and verify persistence across BudgetPlan, BudgetItem, and Recommendation
    db = SessionLocal()
    plan = db.query(BudgetPlan).filter(BudgetPlan.id == plan_id).first()
    assert plan is not None
    assert plan.title == "Master Bohemian Suite"
    assert plan.module_type == "home"
    assert plan.total_budget == 70000.0
    assert plan.allocated_budget == data["budget"]["total_cost"]
    assert plan.remaining_budget == data["budget"]["remaining_budget"]
    assert len(plan.items) > 0
    assert len(plan.recommendations) > 0

    # Verify recommendations are linked to valid products
    for rec in plan.recommendations:
        assert rec.product is not None
        assert rec.product.category.module_type == "home"

    db.close()
