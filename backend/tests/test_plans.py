import pytest
from fastapi.testclient import TestClient
from app.core.database import SessionLocal, init_db
from app.core.security import get_password_hash
from app.main import app
from app.models.budget_plan import BudgetItem, BudgetPlan
from app.models.category import Category
from app.models.product import Product
from app.models.recommendation import Recommendation
from app.models.user import User
from app.seed import seed_database

client = TestClient(app)

USER_A_EMAIL = "plans_user_a@example.com"
USER_A_USERNAME = "plans_user_a"
USER_A_PASSWORD = "UserAPassword123"

USER_B_EMAIL = "plans_user_b@example.com"
USER_B_USERNAME = "plans_user_b"
USER_B_PASSWORD = "UserBPassword123"


@pytest.fixture(scope="module", autouse=True)
def setup_environment():
    init_db()
    seed_database()

    db = SessionLocal()
    # Create User A
    user_a = db.query(User).filter(User.username == USER_A_USERNAME).first()
    if not user_a:
        user_a = User(
            email=USER_A_EMAIL,
            username=USER_A_USERNAME,
            hashed_password=get_password_hash(USER_A_PASSWORD),
            full_name="Plans Test User A",
            is_active=True,
        )
        db.add(user_a)

    # Create User B
    user_b = db.query(User).filter(User.username == USER_B_USERNAME).first()
    if not user_b:
        user_b = User(
            email=USER_B_EMAIL,
            username=USER_B_USERNAME,
            hashed_password=get_password_hash(USER_B_PASSWORD),
            full_name="Plans Test User B",
            is_active=True,
        )
        db.add(user_b)

    db.commit()
    db.close()


def get_token(username: str, password: str) -> str:
    res = client.post(
        "/api/auth/login",
        json={"username_or_email": username, "password": password},
    )
    assert res.status_code == 200
    return res.json()["access_token"]


def create_sample_plan(db, user_id: int, module_type: str, title: str) -> BudgetPlan:
    plan = BudgetPlan(
        user_id=user_id,
        title=title,
        module_type=module_type,
        total_budget=50000.0,
        allocated_budget=45000.0,
        remaining_budget=5000.0,
        currency="INR",
        ai_reasoning=f"Sample reasoning for {title}",
        is_fallback=False,
    )
    db.add(plan)
    db.flush()

    item = BudgetItem(
        plan_id=plan.id,
        category_name="General",
        allocated_amount=45000.0,
        spent_amount=45000.0,
        priority="high",
        reason=f"Item for {title}",
    )
    db.add(item)

    # Attach a product if available
    prod = db.query(Product).first()
    if prod:
        rec = Recommendation(
            plan_id=plan.id,
            product_id=prod.id,
            match_score=0.9,
            recommendation_reason=f"Recommended for {title}",
            is_upgrade=False,
        )
        db.add(rec)

    db.commit()
    saved_plan_id = plan.id
    return saved_plan_id



# =========================================================================
# 1. Unauthenticated GET /api/plans -> 401
# =========================================================================
def test_get_plans_unauthenticated():
    res = client.get("/api/plans")
    assert res.status_code == 401


# =========================================================================
# 2. Authenticated user can retrieve their saved plans
# =========================================================================
def test_get_saved_plans_authenticated():
    token_a = get_token(USER_A_USERNAME, USER_A_PASSWORD)
    db = SessionLocal()
    user_a = db.query(User).filter(User.username == USER_A_USERNAME).first()
    plan_a_id = create_sample_plan(db, user_a.id, "home", "User A Home Plan")
    db.close()

    res = client.get("/api/plans", headers={"Authorization": f"Bearer {token_a}"})
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1
    plan_ids = [item["id"] for item in data["items"]]
    assert plan_a_id in plan_ids


# =========================================================================
# 3. User Isolation (User A cannot see User B's plans)
# =========================================================================
def test_saved_plans_user_isolation():
    token_a = get_token(USER_A_USERNAME, USER_A_PASSWORD)
    token_b = get_token(USER_B_USERNAME, USER_B_PASSWORD)

    db = SessionLocal()
    user_a = db.query(User).filter(User.username == USER_A_USERNAME).first()
    user_b = db.query(User).filter(User.username == USER_B_USERNAME).first()

    plan_b_id = create_sample_plan(db, user_b.id, "party", "User B Private Party Plan")
    db.close()

    # User A requests their plans -> must NOT include User B's plan
    res_a = client.get("/api/plans", headers={"Authorization": f"Bearer {token_a}"})
    assert res_a.status_code == 200
    plan_ids_for_a = [item["id"] for item in res_a.json()["items"]]
    assert plan_b_id not in plan_ids_for_a

    # User B requests their plans -> must include User B's plan
    res_b = client.get("/api/plans", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b.status_code == 200
    plan_ids_for_b = [item["id"] for item in res_b.json()["items"]]
    assert plan_b_id in plan_ids_for_b


# =========================================================================
# 4. Module Filtering (home, party, jewelry, invalid)
# =========================================================================
def test_saved_plans_module_filtering():
    token_a = get_token(USER_A_USERNAME, USER_A_PASSWORD)
    db = SessionLocal()
    user_a = db.query(User).filter(User.username == USER_A_USERNAME).first()

    home_plan_id = create_sample_plan(db, user_a.id, "home", "User A Modular Home")
    party_plan_id = create_sample_plan(db, user_a.id, "party", "User A Birthday Bash")
    jewelry_plan_id = create_sample_plan(db, user_a.id, "jewelry", "User A Gold Wedding Set")
    db.close()

    # Filter: home
    res_home = client.get("/api/plans?module=home", headers={"Authorization": f"Bearer {token_a}"})
    assert res_home.status_code == 200
    items_home = res_home.json()["items"]
    assert all(item["module_type"] == "home" for item in items_home)
    assert any(item["id"] == home_plan_id for item in items_home)
    assert not any(item["id"] == party_plan_id for item in items_home)

    # Filter: party
    res_party = client.get("/api/plans?module=party", headers={"Authorization": f"Bearer {token_a}"})
    assert res_party.status_code == 200
    items_party = res_party.json()["items"]
    assert all(item["module_type"] == "party" for item in items_party)
    assert any(item["id"] == party_plan_id for item in items_party)

    # Filter: jewelry
    res_jewel = client.get("/api/plans?module=jewelry", headers={"Authorization": f"Bearer {token_a}"})
    assert res_jewel.status_code == 200
    items_jewel = res_jewel.json()["items"]
    assert all(item["module_type"] == "jewelry" for item in items_jewel)
    assert any(item["id"] == jewelry_plan_id for item in items_jewel)

    # Filter: invalid module -> 422
    res_inv = client.get("/api/plans?module=automotive_sports", headers={"Authorization": f"Bearer {token_a}"})
    assert res_inv.status_code == 422


# =========================================================================
# 5. GET /api/plans/{plan_id} (Detailed Plan with Items & Recommendations)
# =========================================================================
def test_get_saved_plan_detail():
    token_a = get_token(USER_A_USERNAME, USER_A_PASSWORD)
    db = SessionLocal()
    user_a = db.query(User).filter(User.username == USER_A_USERNAME).first()
    plan_a_id = create_sample_plan(db, user_a.id, "home", "Detailed Living Room Plan")
    db.close()

    res = client.get(f"/api/plans/{plan_a_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == plan_a_id
    assert data["title"] == "Detailed Living Room Plan"
    assert data["module_type"] == "home"
    assert data["total_budget"] == 50000.0
    assert len(data["items"]) >= 1
    assert len(data["recommendations"]) >= 1
    rec = data["recommendations"][0]
    assert rec["product"] is not None
    assert "name" in rec["product"]


# =========================================================================
# 6. GET /api/plans/{plan_id} Nonexistent Plan -> 404
# =========================================================================
def test_get_nonexistent_plan_404():
    token_a = get_token(USER_A_USERNAME, USER_A_PASSWORD)
    res = client.get("/api/plans/999999", headers={"Authorization": f"Bearer {token_a}"})
    assert res.status_code == 404


# =========================================================================
# 7. GET /api/plans/{other_user_plan_id} -> 404 (Privacy/Security)
# =========================================================================
def test_get_other_users_plan_404():
    token_a = get_token(USER_A_USERNAME, USER_A_PASSWORD)
    db = SessionLocal()
    user_b = db.query(User).filter(User.username == USER_B_USERNAME).first()
    plan_b_id = create_sample_plan(db, user_b.id, "party", "User B Secret Party")
    db.close()

    # User A tries to access User B's plan
    res = client.get(f"/api/plans/{plan_b_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert res.status_code == 404


# =========================================================================
# 8. Unauthenticated Detail and Delete -> 401
# =========================================================================
def test_unauthenticated_detail_and_delete():
    res_get = client.get("/api/plans/1")
    assert res_get.status_code == 401

    res_del = client.delete("/api/plans/1")
    assert res_del.status_code == 401


# =========================================================================
# 9. DELETE /api/plans/{plan_id} Own Plan -> 200 & Cascade Verification
# =========================================================================
def test_delete_own_plan_and_cascade():
    token_a = get_token(USER_A_USERNAME, USER_A_PASSWORD)
    db = SessionLocal()
    user_a = db.query(User).filter(User.username == USER_A_USERNAME).first()
    plan_to_delete_id = create_sample_plan(db, user_a.id, "home", "Plan To Delete")
    db.close()

    # Delete the plan
    res = client.delete(f"/api/plans/{plan_to_delete_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert res.status_code == 200
    assert res.json()["plan_id"] == plan_to_delete_id

    # Verify plan is no longer retrievable via API
    res_after = client.get(f"/api/plans/{plan_to_delete_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert res_after.status_code == 404

    # Verify database cascade: BudgetItem and Recommendation rows are removed
    db = SessionLocal()
    items = db.query(BudgetItem).filter(BudgetItem.plan_id == plan_to_delete_id).all()
    assert len(items) == 0

    recs = db.query(Recommendation).filter(Recommendation.plan_id == plan_to_delete_id).all()
    assert len(recs) == 0
    db.close()


# =========================================================================
# 10. DELETE /api/plans/{other_user_plan_id} -> 404 (Cannot Delete Other's Plan)
# =========================================================================
def test_delete_other_users_plan_404():
    token_a = get_token(USER_A_USERNAME, USER_A_PASSWORD)
    db = SessionLocal()
    user_b = db.query(User).filter(User.username == USER_B_USERNAME).first()
    plan_b_id = create_sample_plan(db, user_b.id, "jewelry", "User B Diamond Ring Plan")
    db.close()

    # User A tries to delete User B's plan
    res = client.delete(f"/api/plans/{plan_b_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert res.status_code == 404

    # Verify User B's plan still exists in database
    db = SessionLocal()
    still_exists = db.query(BudgetPlan).filter(BudgetPlan.id == plan_b_id).first()
    assert still_exists is not None
    db.close()

