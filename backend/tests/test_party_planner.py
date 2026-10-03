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
from app.services.party_planner_service import party_planner_service

client = TestClient(app)

TEST_PARTY_USER_EMAIL = "party_planner_user@example.com"
TEST_PARTY_USER_USERNAME = "party_planner_user"
TEST_PARTY_USER_PASSWORD = "PartyPassword123"


@pytest.fixture(scope="module", autouse=True)
def setup_environment():
    init_db()
    seed_database()

    db = SessionLocal()
    user = db.query(User).filter(User.username == TEST_PARTY_USER_USERNAME).first()
    if not user:
        from app.core.security import get_password_hash
        user = User(
            email=TEST_PARTY_USER_EMAIL,
            username=TEST_PARTY_USER_USERNAME,
            hashed_password=get_password_hash(TEST_PARTY_USER_PASSWORD),
            full_name="Party Planner Test User",
            is_active=True,
        )
        db.add(user)
        db.commit()
    db.close()


def get_auth_token():
    res = client.post(
        "/api/auth/login",
        json={"username_or_email": TEST_PARTY_USER_USERNAME, "password": TEST_PARTY_USER_PASSWORD},
    )
    assert res.status_code == 200
    return res.json()["access_token"]


# =========================================================================
# 1. Unauthenticated Request Rejected
# =========================================================================
def test_party_planner_unauthenticated_rejected():
    response = client.post(
        "/api/planner/party",
        json={
            "budget": 100000.0,
            "guest_count": 50,
            "event_type": "birthday",
            "venue_type": "banquet_hall",
        },
    )
    assert response.status_code == 401


# =========================================================================
# 2. Invalid Budget (Zero / Negative)
# =========================================================================
def test_party_planner_invalid_budget():
    token = get_auth_token()
    # Negative budget
    res_neg = client.post(
        "/api/planner/party",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "budget": -5000.0,
            "guest_count": 50,
            "event_type": "birthday",
            "venue_type": "banquet_hall",
        },
    )
    assert res_neg.status_code == 422

    # Zero budget
    res_zero = client.post(
        "/api/planner/party",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "budget": 0.0,
            "guest_count": 50,
            "event_type": "birthday",
            "venue_type": "banquet_hall",
        },
    )
    assert res_zero.status_code == 422


# =========================================================================
# 3. Invalid Guest Count (Zero, Negative, Excess)
# =========================================================================
def test_party_planner_invalid_guest_count():
    token = get_auth_token()
    # Zero guests
    res_zero = client.post(
        "/api/planner/party",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "budget": 50000.0,
            "guest_count": 0,
            "event_type": "birthday",
            "venue_type": "banquet_hall",
        },
    )
    assert res_zero.status_code == 422

    # Negative guests
    res_neg = client.post(
        "/api/planner/party",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "budget": 50000.0,
            "guest_count": -10,
            "event_type": "birthday",
            "venue_type": "banquet_hall",
        },
    )
    assert res_neg.status_code == 422

    # Absurd excessive guest count
    res_excess = client.post(
        "/api/planner/party",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "budget": 50000.0,
            "guest_count": 100000,
            "event_type": "birthday",
            "venue_type": "banquet_hall",
        },
    )
    assert res_excess.status_code == 422


# =========================================================================
# 4. Invalid Event Type
# =========================================================================
def test_party_planner_invalid_event_type():
    token = get_auth_token()
    response = client.post(
        "/api/planner/party",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "budget": 50000.0,
            "guest_count": 50,
            "event_type": "random_rave_carnival",
            "venue_type": "banquet_hall",
        },
    )
    assert response.status_code == 422


# =========================================================================
# 5. Invalid Venue Type
# =========================================================================
def test_party_planner_invalid_venue_type():
    token = get_auth_token()
    response = client.post(
        "/api/planner/party",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "budget": 50000.0,
            "guest_count": 50,
            "event_type": "birthday",
            "venue_type": "spaceship_submarine",
        },
    )
    assert response.status_code == 422


# =========================================================================
# 6. Invalid Duration
# =========================================================================
def test_party_planner_invalid_duration():
    token = get_auth_token()
    # Less than 1 hour
    res_short = client.post(
        "/api/planner/party",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "budget": 50000.0,
            "guest_count": 50,
            "event_type": "birthday",
            "venue_type": "banquet_hall",
            "event_duration_hours": 0.5,
        },
    )
    assert res_short.status_code == 422

    # More than 72 hours
    res_long = client.post(
        "/api/planner/party",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "budget": 50000.0,
            "guest_count": 50,
            "event_type": "birthday",
            "venue_type": "banquet_hall",
            "event_duration_hours": 100.0,
        },
    )
    assert res_long.status_code == 422


# =========================================================================
# 7. Valid Birthday Party Request (Fallback Mode)
# =========================================================================
def test_party_planner_valid_birthday_request():
    token = get_auth_token()
    with patch.object(party_planner_service.ai_service, "is_available", return_value=False):
        response = client.post(
            "/api/planner/party",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "budget": 80000.0,
                "guest_count": 50,
                "event_type": "birthday",
                "venue_type": "banquet_hall",
                "food_preference": "vegetarian",
                "decoration_preference": "balloon",
                "entertainment_preference": "dj",
                "event_duration_hours": 4.0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["module"] == "party"
        assert data["source"] == "deterministic_fallback"
        assert data["plan"]["event_type"] == "birthday"
        assert data["plan"]["guest_count"] == 50
        assert data["budget"]["total_cost"] <= data["budget"]["total_budget"]
        assert data["budget"]["is_within_budget"] is True
        assert len(data["category_allocations"]) == 7
        assert len(data["recommendations"]) > 0


# =========================================================================
# 8. Valid Wedding Request
# =========================================================================
def test_party_planner_valid_wedding_request():
    token = get_auth_token()
    with patch.object(party_planner_service.ai_service, "is_available", return_value=False):
        response = client.post(
            "/api/planner/party",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "budget": 200000.0,
                "guest_count": 150,
                "event_type": "wedding",
                "venue_type": "banquet_hall",
                "food_preference": "multicuisine",
                "decoration_preference": "floral",
                "entertainment_preference": "live_band",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["plan"]["event_type"] == "wedding"
        assert data["budget"]["is_within_budget"] is True
        assert data["budget"]["total_cost"] <= 200000.0


# =========================================================================
# 9. Strict Party Module Isolation (No Home or Jewelry Items)
# =========================================================================
def test_party_planner_module_isolation():
    token = get_auth_token()
    with patch.object(party_planner_service.ai_service, "is_available", return_value=False):
        response = client.post(
            "/api/planner/party",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "budget": 150000.0,
                "guest_count": 80,
                "event_type": "anniversary",
                "venue_type": "hotel",
            },
        )
        assert response.status_code == 200
        data = response.json()
        for rec in data["recommendations"]:
            prod = rec["product"]
            assert prod["module_type"] == "party", f"Leaked non-party product: {prod['name']}"
            assert "bed" not in prod["name"].lower()
            assert "necklace" not in prod["name"].lower()
            assert "sofa" not in prod["name"].lower()


# =========================================================================
# 10. Mocked Gemini AI Recommendation Success
# =========================================================================
def test_party_planner_mocked_gemini_success():
    token = get_auth_token()

    db = SessionLocal()
    party_products = (
        db.query(Product)
        .join(Category, Product.category_id == Category.id)
        .filter(Category.module_type == "party")
        .limit(3)
        .all()
    )
    p1, p2, p3 = party_products[0], party_products[1], party_products[2]
    db.close()

    mock_gemini_response = GeminiStructuredResponse(
        module="party",
        summary="A curated party plan featuring premium catering, venue, and decor.",
        budget_guidance="Excellent allocation balanced across guests.",
        preferences={"event": "birthday", "style": "elegant"},
        recommendations=[
            GeminiProductRec(product_id=p1.id, quantity=1, reason="Core catering package for attendees."),
            GeminiProductRec(product_id=p2.id, quantity=1, reason="Ideal venue setting."),
            GeminiProductRec(product_id=p3.id, quantity=1, reason="Thematic floral decor."),
        ],
        warnings=[],
    )

    with patch.object(party_planner_service.ai_service, "is_available", return_value=True), \
         patch.object(party_planner_service.ai_service, "generate_recommendations", return_value=mock_gemini_response):

        response = client.post(
            "/api/planner/party",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "budget": 150000.0,
                "guest_count": 50,
                "event_type": "birthday",
                "venue_type": "banquet_hall",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "gemini"
        assert len(data["recommendations"]) == 3
        assert data["budget"]["is_within_budget"] is True
        assert data["budget"]["total_cost"] == p1.price + p2.price + p3.price


# =========================================================================
# 11. Gemini Returns Non-Existent or Foreign Module Product ID
# =========================================================================
def test_party_planner_gemini_foreign_and_invalid_product_ids():
    token = get_auth_token()

    db = SessionLocal()
    # Valid party product
    party_prod = (
        db.query(Product)
        .join(Category, Product.category_id == Category.id)
        .filter(Category.module_type == "party")
        .first()
    )
    # Foreign home product
    home_prod = (
        db.query(Product)
        .join(Category, Product.category_id == Category.id)
        .filter(Category.module_type == "home")
        .first()
    )
    db.close()

    mock_gemini_response = GeminiStructuredResponse(
        module="party",
        summary="Gemini test with mixed IDs.",
        budget_guidance="Guidance",
        preferences={},
        recommendations=[
            GeminiProductRec(product_id=party_prod.id, quantity=1, reason="Valid party product."),
            GeminiProductRec(product_id=home_prod.id, quantity=1, reason="Invalid home product attempted."),
            GeminiProductRec(product_id=999999, quantity=1, reason="Non-existent product ID."),
        ],
        warnings=[],
    )

    with patch.object(party_planner_service.ai_service, "is_available", return_value=True), \
         patch.object(party_planner_service.ai_service, "generate_recommendations", return_value=mock_gemini_response):

        response = client.post(
            "/api/planner/party",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "budget": 100000.0,
                "guest_count": 50,
                "event_type": "birthday",
                "venue_type": "banquet_hall",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "gemini"
        rec_ids = [r["product"]["id"] for r in data["recommendations"]]
        assert party_prod.id in rec_ids
        assert home_prod.id not in rec_ids
        assert 999999 not in rec_ids
        # Warnings should reflect omissions
        assert any("non-party module mismatch" in w for w in data["warnings"])
        assert any("not in the catalog" in w for w in data["warnings"])


# =========================================================================
# 12. Gemini Failure / Exception Triggers Fallback
# =========================================================================
def test_party_planner_gemini_failure_fallback():
    token = get_auth_token()

    with patch.object(party_planner_service.ai_service, "is_available", return_value=True), \
         patch.object(party_planner_service.ai_service, "generate_recommendations", side_effect=Exception("API Error")):

        response = client.post(
            "/api/planner/party",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "budget": 75000.0,
                "guest_count": 40,
                "event_type": "birthday",
                "venue_type": "banquet_hall",
            },
        )
        # Should gracefully fallback rather than raising 500
        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "deterministic_fallback"
        assert data["budget"]["is_within_budget"] is True


# =========================================================================
# 13. Budget Enforcement & Overflow Trimming
# =========================================================================
def test_party_planner_budget_enforcement_trimming():
    token = get_auth_token()

    db = SessionLocal()
    party_prods = (
        db.query(Product)
        .join(Category, Product.category_id == Category.id)
        .filter(Category.module_type == "party")
        .all()
    )
    # Pick products that together exceed ₹30,000
    expensive_1 = next(p for p in party_prods if p.price >= 20000.0)
    expensive_2 = next(p for p in party_prods if p.price >= 14000.0 and p.id != expensive_1.id)
    db.close()

    mock_gemini_response = GeminiStructuredResponse(
        module="party",
        summary="Over-budget plan.",
        budget_guidance="Over budget warning",
        preferences={},
        recommendations=[
            GeminiProductRec(product_id=expensive_1.id, quantity=1, reason="Expensive venue."),
            GeminiProductRec(product_id=expensive_2.id, quantity=1, reason="Expensive catering."),
        ],
        warnings=[],
    )

    with patch.object(party_planner_service.ai_service, "is_available", return_value=True), \
         patch.object(party_planner_service.ai_service, "generate_recommendations", return_value=mock_gemini_response):

        # Budget of only 25,000, combined items are > 34,000
        response = client.post(
            "/api/planner/party",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "budget": 25000.0,
                "guest_count": 30,
                "event_type": "birthday",
                "venue_type": "banquet_hall",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["budget"]["is_within_budget"] is True
        assert data["budget"]["total_cost"] <= 25000.0
        assert any("Trimmed" in w for w in data["warnings"])


# =========================================================================
# 14. Guest Count Scales Items & Food Budget
# =========================================================================
def test_party_planner_guest_count_effect():
    token = get_auth_token()

    with patch.object(party_planner_service.ai_service, "is_available", return_value=False):
        # 50 guests
        res_50 = client.post(
            "/api/planner/party",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "budget": 120000.0,
                "guest_count": 50,
                "event_type": "corporate_event",
                "venue_type": "hotel",
            },
        )
        data_50 = res_50.json()

        # 100 guests
        res_100 = client.post(
            "/api/planner/party",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "budget": 120000.0,
                "guest_count": 100,
                "event_type": "corporate_event",
                "venue_type": "hotel",
            },
        )
        data_100 = res_100.json()

        # Per guest food estimation should adjust with guest count
        assert data_50["plan"]["estimated_food_budget_per_guest"] > 0
        assert data_100["plan"]["estimated_food_budget_per_guest"] > 0
        assert data_50["plan"]["estimated_food_budget_per_guest"] != data_100["plan"]["estimated_food_budget_per_guest"]


# =========================================================================
# 15. Database Persistence
# =========================================================================
def test_party_planner_persistence():
    token = get_auth_token()

    with patch.object(party_planner_service.ai_service, "is_available", return_value=False):
        response = client.post(
            "/api/planner/party",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "budget": 95000.0,
                "guest_count": 60,
                "event_type": "college_event",
                "venue_type": "college_campus",
                "title": "Annual Tech Fest Celebration",
            },
        )
        assert response.status_code == 200
        data = response.json()
        plan_id = data["plan_id"]
        assert plan_id is not None

        db = SessionLocal()
        saved_plan = db.query(BudgetPlan).filter(BudgetPlan.id == plan_id).first()
        assert saved_plan is not None
        assert saved_plan.module_type == "party"
        assert saved_plan.title == "Annual Tech Fest Celebration"
        assert saved_plan.total_budget == 95000.0
        assert saved_plan.allocated_budget == data["budget"]["total_cost"]

        # Check budget items and recommendations
        items = db.query(BudgetItem).filter(BudgetItem.plan_id == plan_id).all()
        assert len(items) == len(data["recommendations"])

        recs = db.query(Recommendation).filter(Recommendation.plan_id == plan_id).all()
        assert len(recs) == len(data["recommendations"])
        db.close()
