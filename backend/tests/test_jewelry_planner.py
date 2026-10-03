import io
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from app.core.database import SessionLocal, init_db
from app.main import app
from app.models.budget_plan import BudgetItem, BudgetPlan
from app.models.category import Category
from app.models.product import Product
from app.models.recommendation import Recommendation
from app.models.user import User
from app.schemas.recommendation import GeminiProductRec, GeminiStructuredResponse
from app.seed import seed_database
from app.services.jewelry_planner_service import jewelry_planner_service

client = TestClient(app)

TEST_JEWELRY_USER_EMAIL = "jewelry_planner_user@example.com"
TEST_JEWELRY_USER_USERNAME = "jewelry_planner_user"
TEST_JEWELRY_USER_PASSWORD = "JewelryPassword123"


@pytest.fixture(scope="module", autouse=True)
def setup_environment():
    init_db()
    seed_database()

    db = SessionLocal()
    user = db.query(User).filter(User.username == TEST_JEWELRY_USER_USERNAME).first()
    if not user:
        from app.core.security import get_password_hash
        user = User(
            email=TEST_JEWELRY_USER_EMAIL,
            username=TEST_JEWELRY_USER_USERNAME,
            hashed_password=get_password_hash(TEST_JEWELRY_USER_PASSWORD),
            full_name="Jewelry Planner Test User",
            is_active=True,
        )
        db.add(user)
        db.commit()
    db.close()


def get_auth_token():
    res = client.post(
        "/api/auth/login",
        json={"username_or_email": TEST_JEWELRY_USER_USERNAME, "password": TEST_JEWELRY_USER_PASSWORD},
    )
    assert res.status_code == 200
    return res.json()["access_token"]


def make_dummy_image(format_name: str = "JPEG", size=(100, 100), color=(255, 0, 0)) -> bytes:
    """Creates a real in-memory image for testing."""
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=color)
    img.save(buf, format=format_name)
    return buf.getvalue()


# =========================================================================
# 1. Authentication Required
# =========================================================================
def test_jewelry_planner_unauthenticated_rejected():
    res = client.post(
        "/api/planner/jewelry",
        json={"budget": 50000.0, "occasion": "wedding"},
    )
    assert res.status_code == 401


# =========================================================================
# 2. Valid Jewelry Request (JSON, No Image)
# =========================================================================
def test_jewelry_planner_valid_request():
    token = get_auth_token()
    with patch.object(jewelry_planner_service.ai_service, "is_available", return_value=False):
        res = client.post(
            "/api/planner/jewelry",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "budget": 60000.0,
                "occasion": "wedding",
                "style": "Traditional",
                "preferred_metal": "gold",
                "preferred_color": "ruby-red",
                "jewelry_type": "necklace",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["module"] == "jewelry"
        assert data["source"] == "deterministic_fallback"
        assert data["plan"]["occasion"] == "wedding"
        assert data["plan"]["outfit_analyzed"] is False
        assert data["budget"]["is_within_budget"] is True
        assert data["budget"]["total_cost"] <= 60000.0
        assert len(data["category_allocations"]) > 0
        assert len(data["recommendations"]) > 0


# =========================================================================
# 3. Invalid Budget (Zero / Negative)
# =========================================================================
def test_jewelry_planner_invalid_budget():
    token = get_auth_token()
    # Negative
    res_neg = client.post(
        "/api/planner/jewelry",
        headers={"Authorization": f"Bearer {token}"},
        json={"budget": -2000.0, "occasion": "wedding"},
    )
    assert res_neg.status_code == 422

    # Zero
    res_zero = client.post(
        "/api/planner/jewelry",
        headers={"Authorization": f"Bearer {token}"},
        json={"budget": 0.0, "occasion": "wedding"},
    )
    assert res_zero.status_code == 422


# =========================================================================
# 4. Invalid Occasion
# =========================================================================
def test_jewelry_planner_invalid_occasion():
    token = get_auth_token()
    res = client.post(
        "/api/planner/jewelry",
        headers={"Authorization": f"Bearer {token}"},
        json={"budget": 50000.0, "occasion": "space_mission"},
    )
    assert res.status_code == 422


# =========================================================================
# 5. Invalid Jewelry Type
# =========================================================================
def test_jewelry_planner_invalid_jewelry_type():
    token = get_auth_token()
    res = client.post(
        "/api/planner/jewelry",
        headers={"Authorization": f"Bearer {token}"},
        json={"budget": 50000.0, "occasion": "wedding", "jewelry_type": "tiara_crown_scepter"},
    )
    assert res.status_code == 422


# =========================================================================
# 6. Invalid / Malformed Input
# =========================================================================
def test_jewelry_planner_malformed_input():
    token = get_auth_token()
    res = client.post(
        "/api/planner/jewelry",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        content=b"not-a-valid-json",
    )
    assert res.status_code == 422


# =========================================================================
# 7. Strict Jewelry Module Isolation (No Home or Party Products)
# =========================================================================
def test_jewelry_planner_module_isolation():
    token = get_auth_token()
    with patch.object(jewelry_planner_service.ai_service, "is_available", return_value=False):
        res = client.post(
            "/api/planner/jewelry",
            headers={"Authorization": f"Bearer {token}"},
            json={"budget": 100000.0, "occasion": "wedding"},
        )
        assert res.status_code == 200
        data = res.json()
        for rec in data["recommendations"]:
            prod = rec["product"]
            assert prod["module_type"] == "jewelry", f"Leaked non-jewelry product: {prod['name']}"
            assert "bed" not in prod["name"].lower()
            assert "sofa" not in prod["name"].lower()
            assert "catering" not in prod["name"].lower()
            assert "lawn" not in prod["name"].lower()


# =========================================================================
# 8. Budget Invariant: Total Cost Never Exceeds Budget
# =========================================================================
def test_jewelry_planner_budget_never_exceeded():
    token = get_auth_token()
    with patch.object(jewelry_planner_service.ai_service, "is_available", return_value=False):
        res = client.post(
            "/api/planner/jewelry",
            headers={"Authorization": f"Bearer {token}"},
            json={"budget": 15000.0, "occasion": "birthday", "jewelry_type": "earrings"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["budget"]["total_cost"] <= 15000.0
        assert data["budget"]["is_within_budget"] is True
        assert data["budget"]["over_budget_amount"] == 0.0


# =========================================================================
# 9. Deterministic Budget Calculations
# =========================================================================
def test_jewelry_planner_deterministic_calculations():
    token = get_auth_token()
    with patch.object(jewelry_planner_service.ai_service, "is_available", return_value=False):
        res = client.post(
            "/api/planner/jewelry",
            headers={"Authorization": f"Bearer {token}"},
            json={"budget": 40000.0, "occasion": "engagement"},
        )
        assert res.status_code == 200
        data = res.json()
        b = data["budget"]
        sum_subtotals = sum(r["subtotal"] for r in data["recommendations"])
        assert round(sum_subtotals, 2) == round(b["total_cost"], 2)
        assert round(b["total_budget"] - b["total_cost"], 2) == round(b["remaining_budget"], 2)


# =========================================================================
# 10. Persistence in BudgetPlan, BudgetItem, Recommendation
# =========================================================================
def test_jewelry_planner_persistence():
    token = get_auth_token()
    with patch.object(jewelry_planner_service.ai_service, "is_available", return_value=False):
        res = client.post(
            "/api/planner/jewelry",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "budget": 50000.0,
                "occasion": "wedding",
                "title": "Bridal Traditional Gold Set",
            },
        )
        assert res.status_code == 200
        plan_id = res.json()["plan_id"]
        assert plan_id is not None

        db = SessionLocal()
        saved_plan = db.query(BudgetPlan).filter(BudgetPlan.id == plan_id).first()
        assert saved_plan is not None
        assert saved_plan.module_type == "jewelry"
        assert saved_plan.title == "Bridal Traditional Gold Set"
        assert saved_plan.total_budget == 50000.0

        items = db.query(BudgetItem).filter(BudgetItem.plan_id == plan_id).all()
        assert len(items) == len(res.json()["recommendations"])

        recs = db.query(Recommendation).filter(Recommendation.plan_id == plan_id).all()
        assert len(recs) == len(res.json()["recommendations"])
        db.close()


# =========================================================================
# 11. Mocked Gemini Success (Source: "gemini")
# =========================================================================
def test_jewelry_planner_mocked_gemini_success():
    token = get_auth_token()
    db = SessionLocal()
    j_prods = (
        db.query(Product)
        .join(Category, Product.category_id == Category.id)
        .filter(Category.module_type == "jewelry")
        .limit(2)
        .all()
    )
    p1, p2 = j_prods[0], j_prods[1]
    db.close()

    mock_gemini = GeminiStructuredResponse(
        module="jewelry",
        summary="A curated bridal jewelry ensemble featuring handcrafted gold pieces.",
        budget_guidance="Focus on the central choker piece.",
        preferences={"style": "traditional"},
        recommendations=[
            GeminiProductRec(product_id=p1.id, quantity=1, reason="Centerpiece choker."),
            GeminiProductRec(product_id=p2.id, quantity=1, reason="Matching earrings."),
        ],
        warnings=[],
    )

    with patch.object(jewelry_planner_service.ai_service, "is_available", return_value=True), \
         patch.object(jewelry_planner_service.ai_service, "generate_recommendations", return_value=mock_gemini):

        res = client.post(
            "/api/planner/jewelry",
            headers={"Authorization": f"Bearer {token}"},
            json={"budget": 100000.0, "occasion": "wedding"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["source"] == "gemini"
        assert len(data["recommendations"]) == 2
        assert data["budget"]["total_cost"] == p1.price + p2.price


# =========================================================================
# 12. Gemini Failure / Unavailable Triggers Fallback
# =========================================================================
def test_jewelry_planner_gemini_failure_fallback():
    token = get_auth_token()
    with patch.object(jewelry_planner_service.ai_service, "is_available", return_value=True), \
         patch.object(jewelry_planner_service.ai_service, "generate_recommendations", side_effect=Exception("API Error")):

        res = client.post(
            "/api/planner/jewelry",
            headers={"Authorization": f"Bearer {token}"},
            json={"budget": 50000.0, "occasion": "party"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["source"] == "deterministic_fallback"
        assert data["budget"]["is_within_budget"] is True


# =========================================================================
# 13. Gemini Malformed Response Triggers Fallback
# =========================================================================
def test_jewelry_planner_gemini_malformed_response():
    token = get_auth_token()
    with patch.object(jewelry_planner_service.ai_service, "is_available", return_value=True), \
         patch.object(jewelry_planner_service.ai_service, "generate_recommendations", return_value=None):

        res = client.post(
            "/api/planner/jewelry",
            headers={"Authorization": f"Bearer {token}"},
            json={"budget": 45000.0, "occasion": "engagement"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["source"] == "deterministic_fallback"


# =========================================================================
# 14. Gemini Invalid Product IDs (Omitted and Warned)
# =========================================================================
def test_jewelry_planner_gemini_invalid_product_ids():
    token = get_auth_token()
    db = SessionLocal()
    j_prod = (
        db.query(Product)
        .join(Category, Product.category_id == Category.id)
        .filter(Category.module_type == "jewelry")
        .first()
    )
    db.close()

    mock_gemini = GeminiStructuredResponse(
        module="jewelry",
        summary="Plan with invalid ID.",
        budget_guidance="Note",
        preferences={},
        recommendations=[
            GeminiProductRec(product_id=j_prod.id, quantity=1, reason="Valid piece."),
            GeminiProductRec(product_id=888888, quantity=1, reason="Non-existent product ID."),
        ],
        warnings=[],
    )

    with patch.object(jewelry_planner_service.ai_service, "is_available", return_value=True), \
         patch.object(jewelry_planner_service.ai_service, "generate_recommendations", return_value=mock_gemini):

        res = client.post(
            "/api/planner/jewelry",
            headers={"Authorization": f"Bearer {token}"},
            json={"budget": 80000.0, "occasion": "wedding"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["source"] == "gemini"
        rec_ids = [r["product"]["id"] for r in data["recommendations"]]
        assert j_prod.id in rec_ids
        assert 888888 not in rec_ids
        assert any("not in the catalog" in w for w in data["warnings"])


# =========================================================================
# 15. Gemini Non-Jewelry IDs (Home/Party Items Omitted)
# =========================================================================
def test_jewelry_planner_gemini_non_jewelry_ids():
    token = get_auth_token()
    db = SessionLocal()
    j_prod = (
        db.query(Product)
        .join(Category, Product.category_id == Category.id)
        .filter(Category.module_type == "jewelry")
        .first()
    )
    home_prod = (
        db.query(Product)
        .join(Category, Product.category_id == Category.id)
        .filter(Category.module_type == "home")
        .first()
    )
    db.close()

    mock_gemini = GeminiStructuredResponse(
        module="jewelry",
        summary="Plan with foreign ID.",
        budget_guidance="Note",
        preferences={},
        recommendations=[
            GeminiProductRec(product_id=j_prod.id, quantity=1, reason="Valid piece."),
            GeminiProductRec(product_id=home_prod.id, quantity=1, reason="Leaked home bed."),
        ],
        warnings=[],
    )

    with patch.object(jewelry_planner_service.ai_service, "is_available", return_value=True), \
         patch.object(jewelry_planner_service.ai_service, "generate_recommendations", return_value=mock_gemini):

        res = client.post(
            "/api/planner/jewelry",
            headers={"Authorization": f"Bearer {token}"},
            json={"budget": 80000.0, "occasion": "wedding"},
        )
        assert res.status_code == 200
        data = res.json()
        rec_ids = [r["product"]["id"] for r in data["recommendations"]]
        assert j_prod.id in rec_ids
        assert home_prod.id not in rec_ids
        assert any("non-jewelry module mismatch" in w for w in data["warnings"])


# =========================================================================
# 16. Multipart Request Without Image
# =========================================================================
def test_jewelry_planner_multipart_no_image():
    token = get_auth_token()
    with patch.object(jewelry_planner_service.ai_service, "is_available", return_value=False):
        res = client.post(
            "/api/planner/jewelry",
            headers={"Authorization": f"Bearer {token}"},
            data={"budget": "35000", "occasion": "party", "style": "Modern"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["plan"]["occasion"] == "party"
        assert data["plan"]["outfit_analyzed"] is False


# =========================================================================
# 17. Valid JPEG Image Upload
# =========================================================================
def test_jewelry_planner_valid_jpeg_upload():
    token = get_auth_token()
    jpeg_bytes = make_dummy_image(format_name="JPEG")

    with patch.object(jewelry_planner_service.ai_service, "is_available", return_value=False):
        res = client.post(
            "/api/planner/jewelry",
            headers={"Authorization": f"Bearer {token}"},
            data={"budget": "50000", "occasion": "wedding", "style": "Traditional"},
            files={"outfit_image": ("outfit.jpg", jpeg_bytes, "image/jpeg")},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["plan"]["outfit_analyzed"] is True


# =========================================================================
# 18. Valid PNG Image Upload
# =========================================================================
def test_jewelry_planner_valid_png_upload():
    token = get_auth_token()
    png_bytes = make_dummy_image(format_name="PNG")

    with patch.object(jewelry_planner_service.ai_service, "is_available", return_value=False):
        res = client.post(
            "/api/planner/jewelry",
            headers={"Authorization": f"Bearer {token}"},
            data={"budget": "50000", "occasion": "reception", "occasion": "wedding"},
            files={"outfit_image": ("outfit.png", png_bytes, "image/png")},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["plan"]["outfit_analyzed"] is True


# =========================================================================
# 19. Valid WEBP Image Upload
# =========================================================================
def test_jewelry_planner_valid_webp_upload():
    token = get_auth_token()
    webp_bytes = make_dummy_image(format_name="WEBP")

    with patch.object(jewelry_planner_service.ai_service, "is_available", return_value=False):
        res = client.post(
            "/api/planner/jewelry",
            headers={"Authorization": f"Bearer {token}"},
            data={"budget": "50000", "occasion": "formal_event"},
            files={"outfit_image": ("outfit.webp", webp_bytes, "image/webp")},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["plan"]["outfit_analyzed"] is True


# =========================================================================
# 20. Unsupported Image Type Rejected
# =========================================================================
def test_jewelry_planner_unsupported_image_rejected():
    token = get_auth_token()
    res = client.post(
        "/api/planner/jewelry",
        headers={"Authorization": f"Bearer {token}"},
        data={"budget": "50000", "occasion": "wedding"},
        files={"outfit_image": ("malicious.sh", b"#!/bin/bash\necho hack", "application/x-sh")},
    )
    assert res.status_code == 400
    assert "Unsupported image type" in res.json()["detail"]


# =========================================================================
# 21. Oversized Image Rejected (> 5MB)
# =========================================================================
def test_jewelry_planner_oversized_image_rejected():
    token = get_auth_token()
    huge_bytes = b"0" * (6 * 1024 * 1024)  # 6 MB
    res = client.post(
        "/api/planner/jewelry",
        headers={"Authorization": f"Bearer {token}"},
        data={"budget": "50000", "occasion": "wedding"},
        files={"outfit_image": ("huge.jpg", huge_bytes, "image/jpeg")},
    )
    assert res.status_code == 413
    assert "exceeds maximum allowed size" in res.json()["detail"]


# =========================================================================
# 22. Corrupt Image Rejected
# =========================================================================
def test_jewelry_planner_corrupt_image_rejected():
    token = get_auth_token()
    corrupt_bytes = b"\xff\xd8\xff\xe0" + b"corrupt random bytes not an image"
    res = client.post(
        "/api/planner/jewelry",
        headers={"Authorization": f"Bearer {token}"},
        data={"budget": "50000", "occasion": "wedding"},
        files={"outfit_image": ("corrupt.jpg", corrupt_bytes, "image/jpeg")},
    )
    assert res.status_code == 400
    assert "Corrupt or invalid image" in res.json()["detail"]


# =========================================================================
# 23. Image Passed Only From Backend to Gemini
# =========================================================================
def test_jewelry_planner_image_passed_to_gemini_backend_only():
    token = get_auth_token()
    jpeg_bytes = make_dummy_image(format_name="JPEG")

    mock_gemini = GeminiStructuredResponse(
        module="jewelry",
        summary="Image-based outfit jewelry plan.",
        budget_guidance="Harmonious jewelry match.",
        preferences={},
        recommendations=[],
        warnings=[],
    )

    with patch.object(jewelry_planner_service.ai_service, "is_available", return_value=True), \
         patch.object(jewelry_planner_service.ai_service, "generate_recommendations", return_value=mock_gemini) as mock_gen:

        res = client.post(
            "/api/planner/jewelry",
            headers={"Authorization": f"Bearer {token}"},
            data={"budget": "50000", "occasion": "traditional_event"},
            files={"outfit_image": ("outfit.jpg", jpeg_bytes, "image/jpeg")},
        )
        assert res.status_code == 200
        # Check that generate_recommendations was called with image_bytes and image_mime_type
        mock_gen.assert_called_once()
        _, kwargs = mock_gen.call_args
        assert kwargs.get("image_bytes") == jpeg_bytes
        assert kwargs.get("image_mime_type") == "image/jpeg"


# =========================================================================
# 24. Image Privacy & Identity Guardrail Behavior
# =========================================================================
def test_jewelry_planner_image_privacy_prompt_guardrails():
    db = SessionLocal()
    candidates = (
        db.query(Product)
        .join(Category, Product.category_id == Category.id)
        .filter(Category.module_type == "jewelry")
        .limit(3)
        .all()
    )
    db.close()

    prompt_with_image = jewelry_planner_service.ai_service.build_prompt(
        module="jewelry",
        budget=50000.0,
        preferences="Occasion: Wedding. Traditional styling.",
        candidates=candidates,
        has_image=True,
    )

    # Prompt must contain strict anti-facial recognition and privacy directives
    assert "STRICT PRIVACY RULE" in prompt_with_image
    assert "DO NOT identify or describe human faces, person identity" in prompt_with_image
    assert "No personal identification is allowed" in prompt_with_image


# =========================================================================
# 25. Fallback Still Produces Valid Plan With Budget Invariants
# =========================================================================
def test_jewelry_planner_fallback_produces_valid_plan():
    token = get_auth_token()
    with patch.object(jewelry_planner_service.ai_service, "is_available", return_value=False):
        res = client.post(
            "/api/planner/jewelry",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "budget": 20000.0,
                "occasion": "party",
                "style": "Minimalist",
                "preferred_metal": "silver",
                "preferred_color": "diamond",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["source"] == "deterministic_fallback"
        assert data["budget"]["is_within_budget"] is True
        assert data["budget"]["total_cost"] <= 20000.0
        assert data["budget"]["total_cost"] > 0
        assert len(data["recommendations"]) > 0
