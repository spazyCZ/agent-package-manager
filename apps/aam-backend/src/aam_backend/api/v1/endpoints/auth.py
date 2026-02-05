"""Authentication endpoints."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from aam_backend.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)

router = APIRouter()


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """Register request schema."""

    email: EmailStr
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Token refresh request schema."""

    refresh_token: str


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest) -> TokenResponse:
    """Authenticate user and return tokens."""
    # TODO: Implement actual user lookup from database
    # For now, mock validation
    if request.email == "test@example.com" and request.password == "password":
        return TokenResponse(
            access_token=create_access_token(request.email),
            refresh_token=create_refresh_token(request.email),
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest) -> TokenResponse:
    """Register a new user."""
    # TODO: Implement actual user creation in database
    _ = hash_password(request.password)

    return TokenResponse(
        access_token=create_access_token(request.email),
        refresh_token=create_refresh_token(request.email),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest) -> TokenResponse:
    """Refresh access token."""
    from aam_backend.core.security import decode_token

    payload = decode_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return TokenResponse(
        access_token=create_access_token(subject),
        refresh_token=create_refresh_token(subject),
    )


@router.post("/logout")
async def logout() -> dict[str, str]:
    """Logout user (invalidate tokens)."""
    # TODO: Implement token blacklist
    return {"message": "Logged out successfully"}
