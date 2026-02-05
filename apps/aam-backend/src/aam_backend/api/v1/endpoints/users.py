"""User endpoints."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

router = APIRouter()


class UserResponse(BaseModel):
    """User response schema."""

    id: str
    email: EmailStr
    username: str
    avatar_url: str | None = None
    created_at: str


class UserUpdateRequest(BaseModel):
    """User update request schema."""

    username: str | None = None
    avatar_url: str | None = None


@router.get("/me", response_model=UserResponse)
async def get_current_user() -> UserResponse:
    """Get current authenticated user."""
    # TODO: Get user from JWT token
    return UserResponse(
        id="user-123",
        email="test@example.com",
        username="testuser",
        avatar_url=None,
        created_at="2024-01-01T00:00:00Z",
    )


@router.patch("/me", response_model=UserResponse)
async def update_current_user(request: UserUpdateRequest) -> UserResponse:
    """Update current user profile."""
    # TODO: Update user in database
    return UserResponse(
        id="user-123",
        email="test@example.com",
        username=request.username or "testuser",
        avatar_url=request.avatar_url,
        created_at="2024-01-01T00:00:00Z",
    )


@router.get("/{username}", response_model=UserResponse)
async def get_user(username: str) -> UserResponse:
    """Get user by username."""
    # TODO: Lookup user in database
    if username == "testuser":
        return UserResponse(
            id="user-123",
            email="test@example.com",
            username="testuser",
            avatar_url=None,
            created_at="2024-01-01T00:00:00Z",
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found",
    )
