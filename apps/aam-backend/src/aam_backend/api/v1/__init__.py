"""API v1 router."""

from fastapi import APIRouter

from aam_backend.api.v1.endpoints import audit, auth, packages, users

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(packages.router, prefix="/packages", tags=["packages"])
router.include_router(audit.router, prefix="/audit-log", tags=["audit"])