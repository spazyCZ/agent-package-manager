"""Package endpoints."""

from fastapi import APIRouter, HTTPException, Query, UploadFile, status
from pydantic import BaseModel

router = APIRouter()


class PackageVersion(BaseModel):
    """Package version schema."""

    version: str
    published_at: str
    downloads: int
    size: int


class PackageResponse(BaseModel):
    """Package response schema."""

    name: str
    description: str | None
    latest_version: str
    author: str
    license: str | None
    homepage: str | None
    repository: str | None
    keywords: list[str]
    versions: list[PackageVersion]
    created_at: str
    updated_at: str
    downloads: int


class PackageListResponse(BaseModel):
    """Package list response schema."""

    packages: list[PackageResponse]
    total: int
    page: int
    per_page: int


class PackageSearchResponse(BaseModel):
    """Package search response schema."""

    results: list[PackageResponse]
    total: int
    query: str


class PublishResponse(BaseModel):
    """Publish response schema."""

    name: str
    version: str
    message: str


@router.get("", response_model=PackageListResponse)
async def list_packages(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    sort: str = Query(default="downloads", pattern="^(name|downloads|updated)$"),
) -> PackageListResponse:
    """List all packages with pagination."""
    # TODO: Implement actual database query
    return PackageListResponse(
        packages=[],
        total=0,
        page=page,
        per_page=per_page,
    )


@router.get("/search", response_model=PackageSearchResponse)
async def search_packages(
    q: str = Query(..., min_length=1),
    type: str | None = Query(default=None, pattern="^(agent|skill|tool)$"),
    limit: int = Query(default=20, ge=1, le=100),
) -> PackageSearchResponse:
    """Search for packages."""
    # TODO: Implement actual search
    return PackageSearchResponse(
        results=[],
        total=0,
        query=q,
    )


@router.get("/{name}", response_model=PackageResponse)
async def get_package(name: str) -> PackageResponse:
    """Get package details."""
    # TODO: Lookup package in database
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Package '{name}' not found",
    )


@router.get("/{name}/{version}")
async def get_package_version(name: str, version: str) -> dict[str, object]:
    """Get specific package version details."""
    # TODO: Lookup package version
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Package '{name}@{version}' not found",
    )


@router.get("/{name}/{version}/download")
async def download_package(name: str, version: str) -> dict[str, str]:
    """Get download URL for package."""
    # TODO: Generate signed download URL
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Package '{name}@{version}' not found",
    )


@router.post("", response_model=PublishResponse, status_code=status.HTTP_201_CREATED)
async def publish_package(file: UploadFile) -> PublishResponse:
    """Publish a new package or version."""
    # TODO: Implement package upload and processing
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided",
        )

    return PublishResponse(
        name="example-package",
        version="1.0.0",
        message="Package published successfully",
    )


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def unpublish_package(name: str) -> None:
    """Unpublish a package (admin only)."""
    # TODO: Implement unpublish logic
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Package '{name}' not found",
    )


@router.delete("/{name}/{version}", status_code=status.HTTP_204_NO_CONTENT)
async def unpublish_version(name: str, version: str) -> None:
    """Unpublish a specific version."""
    # TODO: Implement version unpublish logic
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Package '{name}@{version}' not found",
    )
