from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Username must be 3-50 characters with letters, numbers, hyphens, or underscores only.",
    )
    full_name: Optional[str] = Field(None, max_length=150)


class UserCreate(UserBase):
    password: str = Field(
        ...,
        min_length=6,
        max_length=100,
        description="Password must be between 6 and 100 characters.",
    )


class UserLogin(BaseModel):
    username_or_email: str = Field(..., min_length=3, description="Username or registered email address")
    password: str = Field(..., min_length=1, description="Account password")


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None
