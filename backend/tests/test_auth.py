import pytest
from fastapi.testclient import TestClient
from app.core.database import SessionLocal, init_db
from app.main import app
from app.models.user import User

client = TestClient(app)


@pytest.fixture(autouse=True)
def ensure_db():
    init_db()


def test_successful_registration():
    email = "testuser_reg@example.com"
    username = "testuser_reg"
    password = "SecretPassword123"

    # Clean up if existing from previous run
    db = SessionLocal()
    existing = db.query(User).filter((User.email == email) | (User.username == username)).first()
    if existing:
        db.delete(existing)
        db.commit()
    db.close()

    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "username": username,
            "password": password,
            "full_name": "Test User Regular",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == email
    assert data["username"] == username
    assert data["full_name"] == "Test User Regular"
    assert "id" in data
    assert "password" not in data  # Never expose password in response


def test_password_not_stored_as_plaintext():
    email = "testuser_reg@example.com"
    password = "SecretPassword123"

    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    db.close()

    assert user is not None
    # Password must NEVER be stored in plaintext
    assert user.hashed_password != password
    # Must be a valid bcrypt hash format ($2b$ or $2a$)
    assert user.hashed_password.startswith("$2")


def test_duplicate_email_registration():
    email = "testuser_reg@example.com"
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "username": "different_username",
            "password": "ValidPassword123",
            "full_name": "Duplicate Email Attempt",
        },
    )
    assert response.status_code == 400
    assert "email address already exists" in response.json()["detail"].lower()


def test_duplicate_username_registration():
    username = "testuser_reg"
    response = client.post(
        "/api/auth/register",
        json={
            "email": "different_email@example.com",
            "username": username,
            "password": "ValidPassword123",
            "full_name": "Duplicate Username Attempt",
        },
    )
    assert response.status_code == 400
    assert "username is already taken" in response.json()["detail"].lower()


def test_invalid_registration_inputs():
    # Invalid email format
    res_email = client.post(
        "/api/auth/register",
        json={
            "email": "not-an-email",
            "username": "validuser1",
            "password": "ValidPassword123",
        },
    )
    assert res_email.status_code == 422

    # Password too short (less than 6 chars)
    res_pwd = client.post(
        "/api/auth/register",
        json={
            "email": "valid_user2@example.com",
            "username": "validuser2",
            "password": "123",
        },
    )
    assert res_pwd.status_code == 422


def test_successful_login_with_username():
    response = client.post(
        "/api/auth/login",
        json={
            "username_or_email": "testuser_reg",
            "password": "SecretPassword123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "testuser_reg"
    assert data["user"]["email"] == "testuser_reg@example.com"


def test_successful_login_with_email():
    response = client.post(
        "/api/auth/login",
        json={
            "username_or_email": "testuser_reg@example.com",
            "password": "SecretPassword123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "testuser_reg"


def test_login_incorrect_password():
    response = client.post(
        "/api/auth/login",
        json={
            "username_or_email": "testuser_reg",
            "password": "WrongPassword999",
        },
    )
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


def test_login_invalid_credentials_nonexistent_user():
    response = client.post(
        "/api/auth/login",
        json={
            "username_or_email": "non_existent_user_999",
            "password": "SomePassword123",
        },
    )
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


def test_authenticated_get_me():
    # 1. Login to get token
    login_res = client.post(
        "/api/auth/login",
        json={
            "username_or_email": "testuser_reg",
            "password": "SecretPassword123",
        },
    )
    token = login_res.json()["access_token"]

    # 2. Access /api/auth/me with Bearer token
    me_res = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    data = me_res.json()
    assert data["username"] == "testuser_reg"
    assert data["email"] == "testuser_reg@example.com"


def test_unauthenticated_access_get_me():
    # Without Authorization header
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert "credentials" in response.json()["detail"].lower()


def test_invalid_token_access_get_me():
    # With forged/tampered token
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid_tampered_jwt_token"},
    )
    assert response.status_code == 401
    assert "credentials" in response.json()["detail"].lower()
