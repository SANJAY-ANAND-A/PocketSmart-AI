from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from app.core.database import SessionLocal, init_db
from app.main import app
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.schemas.recommendation import (
    GeminiInterpretedPreferences,
    GeminiProductRec,
    GeminiStructuredResponse,
)
from app.seed import seed_database
from app.services.gemini_service import GeminiService
from app.services.recommendation_engine import RecommendationEngine, recommendation_engine

client = TestClient(app)

TEST_USER_EMAIL = "ai_rec_tester@example.com"
TEST_USER_USERNAME = "ai_rec_tester"
TEST_USER_PASSWORD = "TestAIPassword123"


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
            full_name="AI Recommendation Tester",
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
# 1. Gemini Service Unit Tests (Mocking SDK calls)
# =========================================================================

def test_gemini_service_availability_check():
    svc_no_key = GeminiService(api_key="")
    assert svc_no_key.is_available() is False

    svc_with_key = GeminiService(api_key="valid_sample_key_123")
    assert svc_with_key.is_available() is True


def test_gemini_service_valid_structured_parsing():
    db = SessionLocal()
    candidates = db.query(Product).limit(3).all()
    db.close()

    mock_json_payload = {
        "module": "home",
        "summary": "Tailored minimalist bedroom setup.",
        "budget_guidance": "Allocate majority to high-quality sleep setup.",
        "preferences": {
            "style": "Minimalist",
            "priority": "Comfort",
            "key_aspects": ["wood", "clean lines"],
        },
        "recommendations": [
            {"product_id": candidates[0].id, "quantity": 1, "reason": "Durable frame"}
        ],
        "warnings": [],
    }

    mock_response = MagicMock()
    mock_response.text = '{"module": "home", "summary": "Tailored minimalist bedroom setup.", "budget_guidance": "Allocate majority to high-quality sleep setup.", "preferences": {"style": "Minimalist", "priority": "Comfort", "key_aspects": ["wood", "clean lines"]}, "recommendations": [{"product_id": ' + str(candidates[0].id) + ', "quantity": 1, "reason": "Durable frame"}], "warnings": []}'

    with patch("app.services.gemini_service.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        svc = GeminiService(api_key="test_api_key")
        result = svc.generate_recommendations("home", 50000.0, "Minimalist bed", candidates)

        assert result is not None
        assert result.module == "home"
        assert len(result.recommendations) == 1
        assert result.recommendations[0].product_id == candidates[0].id


def test_gemini_service_invalid_json_handling():
    db = SessionLocal()
    candidates = db.query(Product).limit(2).all()
    db.close()

    mock_response = MagicMock()
    mock_response.text = "This is not valid JSON string at all from LLM!"

    with patch("app.services.gemini_service.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        svc = GeminiService(api_key="test_api_key")
        result = svc.generate_recommendations("home", 50000.0, "Minimalist bed", candidates)

        # Must gracefully return None without raising exception
        assert result is None


def test_gemini_service_invalid_schema_handling():
    db = SessionLocal()
    candidates = db.query(Product).limit(2).all()
    db.close()

    # Missing required 'summary' and 'module' fields
    mock_response = MagicMock()
    mock_response.text = '{"some_unrelated_key": 123}'

    with patch("app.services.gemini_service.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        svc = GeminiService(api_key="test_api_key")
        result = svc.generate_recommendations("home", 50000.0, "Minimalist bed", candidates)

        assert result is None


def test_gemini_service_api_exception_handling():
    db = SessionLocal()
    candidates = db.query(Product).limit(2).all()
    db.close()

    with patch("app.services.gemini_service.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = RuntimeError("Google API Quota Exceeded or Timeout")
        mock_client_cls.return_value = mock_client

        svc = GeminiService(api_key="test_api_key")
        result = svc.generate_recommendations("home", 50000.0, "Minimalist bed", candidates)

        assert result is None


# =========================================================================
# 2. Recommendation Endpoint Integration Tests
# =========================================================================

def test_recommendation_requires_authentication():
    response = client.post(
        "/api/recommendations",
        json={"module": "home", "budget": 50000.0, "preferences": "Living room sofa"},
    )
    assert response.status_code == 401


def test_recommendation_invalid_module():
    token = get_auth_token()
    response = client.post(
        "/api/recommendations",
        headers={"Authorization": f"Bearer {token}"},
        json={"module": "automotive", "budget": 50000.0, "preferences": "Sedan car"},
    )
    assert response.status_code == 422


def test_recommendation_invalid_budget():
    token = get_auth_token()
    response = client.post(
        "/api/recommendations",
        headers={"Authorization": f"Bearer {token}"},
        json={"module": "home", "budget": -100.0, "preferences": "Living room sofa"},
    )
    assert response.status_code == 422


def test_recommendation_gemini_success_flow():
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

    # Mock Gemini returning valid recommendations
    mock_gemini_output = GeminiStructuredResponse(
        module="home",
        summary="A balanced Scandinavian interior matching your ₹50,000 budget.",
        budget_guidance="Invest in the main storage bed first.",
        preferences=GeminiInterpretedPreferences(
            style="Scandinavian",
            priority="Aesthetics",
            key_aspects=["wood", "storage"],
        ),
        recommendations=[
            GeminiProductRec(
                product_id=home_prods[0].id,
                quantity=1,
                reason="Fits the requested Scandinavian aesthetic perfectly.",
            ),
            GeminiProductRec(
                product_id=home_prods[1].id,
                quantity=1,
                reason="Adds complementary practical seating.",
            ),
        ],
        warnings=[],
    )

    with patch.object(recommendation_engine.ai_service, "is_available", return_value=True):
        with patch.object(recommendation_engine.ai_service, "generate_recommendations", return_value=mock_gemini_output):
            response = client.post(
                "/api/recommendations",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "module": "home",
                    "budget": 60000.0,
                    "preferences": "I want a Scandinavian bedroom with wood finish.",
                    "save_plan": True,
                    "title": "Scandinavian Bedroom Recommendation",
                },
            )

    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "gemini"
    assert data["module"] == "home"
    assert "Scandinavian" in data["summary"]
    assert len(data["recommendations"]) == 2
    assert data["budget"]["is_within_budget"] is True
    assert data["budget"]["currency"] == "INR"
    assert data["budget"]["currency_symbol"] == "₹"
    assert data["plan_id"] is not None


def test_recommendation_deterministic_fallback_when_gemini_unavailable():
    token = get_auth_token()

    # Simulate Gemini being unavailable (missing key or API failure returning None)
    with patch.object(recommendation_engine.ai_service, "is_available", return_value=False):
        response = client.post(
            "/api/recommendations",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "module": "home",
                "budget": 45000.0,
                "preferences": "Need a comfortable queen bed and bedside lighting.",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "deterministic_fallback"
    assert data["module"] == "home"
    assert len(data["recommendations"]) > 0
    assert data["budget"]["is_within_budget"] is True
    assert any("rule-based" in w.lower() for w in data["warnings"])


def test_recommendation_gemini_returns_nonexistent_product_id():
    token = get_auth_token()
    db = SessionLocal()
    real_prod = (
        db.query(Product)
        .join(Category, Product.category_id == Category.id)
        .filter(Category.module_type == "party")
        .first()
    )
    db.close()

    # Gemini returns one valid product and one non-existent ID
    mock_gemini_output = GeminiStructuredResponse(
        module="party",
        summary="Party plan with DJ and catering.",
        recommendations=[
            GeminiProductRec(product_id=real_prod.id, quantity=1, reason="Great event choice"),
            GeminiProductRec(product_id=999999, quantity=1, reason="Invented non-existent product"),
        ],
    )

    with patch.object(recommendation_engine.ai_service, "is_available", return_value=True):
        with patch.object(recommendation_engine.ai_service, "generate_recommendations", return_value=mock_gemini_output):
            response = client.post(
                "/api/recommendations",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "module": "party",
                    "budget": 30000.0,
                    "preferences": "Outdoor party setup for friends.",
                },
            )

    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "gemini"
    # The non-existent product should be filtered out
    rec_ids = [r["product"]["id"] for r in data["recommendations"]]
    assert 999999 not in rec_ids
    assert real_prod.id in rec_ids
    assert any("999999" in w for w in data["warnings"])


def test_recommendation_over_budget_pruning_adjustment():
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

    # Two items whose combined price is higher than 30,000
    total_items_cost = home_prods[0].price + home_prods[1].price
    tight_budget = min(home_prods[0].price, home_prods[1].price) + 2000.0

    mock_gemini_output = GeminiStructuredResponse(
        module="home",
        summary="Luxurious setup.",
        recommendations=[
            GeminiProductRec(product_id=home_prods[0].id, quantity=1, reason="Essential"),
            GeminiProductRec(product_id=home_prods[1].id, quantity=1, reason="Secondary item"),
        ],
    )

    with patch.object(recommendation_engine.ai_service, "is_available", return_value=True):
        with patch.object(recommendation_engine.ai_service, "generate_recommendations", return_value=mock_gemini_output):
            response = client.post(
                "/api/recommendations",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "module": "home",
                    "budget": tight_budget,
                    "preferences": "Living room setup on a strict budget.",
                },
            )

    assert response.status_code == 200
    data = response.json()
    # The engine should deterministically prune or trim to satisfy budget
    assert data["budget"]["total_cost"] <= tight_budget
    assert data["budget"]["is_within_budget"] is True
    assert any("trimmed" in w.lower() for w in data["warnings"])


def test_recommendations_support_all_three_modules():
    token = get_auth_token()

    for mod in ["home", "party", "jewelry"]:
        with patch.object(recommendation_engine.ai_service, "is_available", return_value=False):
            res = client.post(
                "/api/recommendations",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "module": mod,
                    "budget": 35000.0,
                    "preferences": f"Planning my {mod} requirements with high quality.",
                },
            )
            assert res.status_code == 200
            data = res.json()
            assert data["module"] == mod
            assert len(data["recommendations"]) > 0
            for r in data["recommendations"]:
                assert r["product"]["module_type"] == mod
