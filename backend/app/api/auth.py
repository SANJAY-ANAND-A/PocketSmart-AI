from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserLogin, UserResponse

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description="Registers a new user with email, unique username, and secure password. Passwords are encrypted with bcrypt.",
)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db),
) -> UserResponse:
    # 1. Check duplicate email
    normalized_email = user_in.email.lower()
    if db.query(User).filter(User.email == normalized_email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    # 2. Check duplicate username
    normalized_username = user_in.username.lower()
    if db.query(User).filter(User.username == normalized_username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This username is already taken. Please choose another.",
        )

    # 3. Hash password and persist user
    hashed_pwd = get_password_hash(user_in.password)
    user = User(
        email=normalized_email,
        username=normalized_username,
        full_name=user_in.full_name,
        hashed_password=hashed_pwd,
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and obtain JWT token",
    description="Authenticates with username or email along with the password, returning a signed JWT access token.",
)
def login(
    login_in: UserLogin,
    db: Session = Depends(get_db),
) -> Token:
    identifier = login_in.username_or_email.strip().lower()

    # Allow login with either registered username or email
    user = (
        db.query(User)
        .filter((User.username == identifier) | (User.email == identifier))
        .first()
    )

    if not user or not verify_password(login_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive account. Please contact support.",
        )

    # Generate JWT Bearer token
    access_token = create_access_token(
        subject=user.id,
        extra_claims={"username": user.username, "email": user.email},
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
    description="Validates the Authorization Bearer JWT token and returns the current user profile.",
)
def read_current_user(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return current_user
