"""Package endpoints.

Provides CRUD endpoints for both scoped (``@scope/name``) and unscoped
(``name``) packages.

**Important:** Scoped routes (``/@{scope}/{name}``) are defined *before*
unscoped routes (``/{name}``) so that FastAPI does not misinterpret a scoped
path like ``/@author/my-pkg`` as ``{name}/{version}``.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging

from fastapi import APIRouter, HTTPException, Query, UploadFile, status
from pydantic import BaseModel

from aam_backend.core.naming import (
    format_package_name,
    parse_package_name,
    validate_package_name,
)

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# SCHEMAS                                                                      #
#                                                                              #
################################################################################

router = APIRouter()


class PackageVersionSchema(BaseModel):
    """Package version schema."""

    version: str
    published_at: str
    downloads: int
    size: int


class PackageResponse(BaseModel):
    """Package response schema.

    The ``scope`` field is an empty string for unscoped packages.
    The ``name`` field always contains the full name (e.g. ``@author/my-pkg``
    or ``my-pkg``).
    """

    name: str
    scope: str
    description: str | None
    latest_version: str
    author: str
    license: str | None
    homepage: str | None
    repository: str | None
    keywords: list[str]
    versions: list[PackageVersionSchema]
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
    scope: str
    version: str
    message: str


################################################################################
#                                                                              #
# HELPER FUNCTIONS                                                             #
#                                                                              #
################################################################################


def _validate_scope(scope: str) -> None:
    """Validate scope path parameter.

    Args:
        scope: The scope string (without ``@``).

    Raises:
        HTTPException: If the scope is invalid.
    """
    # Reconstruct full name for validation; we just need the scope part
    if not validate_package_name(f"@{scope}/a"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scope: '{scope}'",
        )


def _validate_name(name: str) -> None:
    """Validate name path parameter.

    Args:
        name: The package name (without scope).

    Raises:
        HTTPException: If the name is invalid.
    """
    if not validate_package_name(name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid package name: '{name}'",
        )


async def _get_package_impl(scope: str, name: str) -> PackageResponse:
    """Internal helper to get a package by scope and name.

    Args:
        scope: Package scope (empty string for unscoped).
        name: Package name (without scope prefix).

    Returns:
        PackageResponse for the requested package.

    Raises:
        HTTPException: If the package is not found.
    """
    full_name = format_package_name(scope, name)
    logger.info(f"Getting package: full_name='{full_name}'")

    # TODO: Lookup package in database using (scope, name) pair
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Package '{full_name}' not found",
    )


async def _get_version_impl(
    scope: str, name: str, version: str
) -> dict[str, object]:
    """Internal helper to get a specific version of a package.

    Args:
        scope: Package scope (empty string for unscoped).
        name: Package name (without scope prefix).
        version: The semver version string.

    Returns:
        Version metadata dict.

    Raises:
        HTTPException: If the package version is not found.
    """
    full_name = format_package_name(scope, name)
    logger.info(
        f"Getting package version: full_name='{full_name}', version='{version}'"
    )

    # TODO: Lookup package version
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Package '{full_name}@{version}' not found",
    )


async def _download_impl(
    scope: str, name: str, version: str
) -> dict[str, str]:
    """Internal helper to get download URL for a package.

    Args:
        scope: Package scope (empty string for unscoped).
        name: Package name (without scope prefix).
        version: The semver version string.

    Returns:
        Dict with download URL.

    Raises:
        HTTPException: If the package version is not found.
    """
    full_name = format_package_name(scope, name)
    logger.info(
        f"Downloading package: full_name='{full_name}', version='{version}'"
    )

    # TODO: Generate signed download URL
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Package '{full_name}@{version}' not found",
    )


async def _delete_package_impl(scope: str, name: str) -> None:
    """Internal helper to delete a package.

    Args:
        scope: Package scope (empty string for unscoped).
        name: Package name (without scope prefix).

    Raises:
        HTTPException: If the package is not found.
    """
    full_name = format_package_name(scope, name)
    logger.info(f"Deleting package: full_name='{full_name}'")

    # TODO: Implement unpublish logic
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Package '{full_name}' not found",
    )


async def _delete_version_impl(
    scope: str, name: str, version: str
) -> None:
    """Internal helper to delete a package version.

    Args:
        scope: Package scope (empty string for unscoped).
        name: Package name (without scope prefix).
        version: The semver version string.

    Raises:
        HTTPException: If the package version is not found.
    """
    full_name = format_package_name(scope, name)
    logger.info(
        f"Deleting package version: full_name='{full_name}', version='{version}'"
    )

    # TODO: Implement version unpublish logic
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Package '{full_name}@{version}' not found",
    )


################################################################################
#                                                                              #
# LIST / SEARCH ENDPOINTS                                                      #
#                                                                              #
################################################################################


@router.get("", response_model=PackageListResponse)
async def list_packages(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    sort: str = Query(default="downloads", pattern="^(name|downloads|updated)$"),
) -> PackageListResponse:
    """List all packages with pagination."""
    logger.info(f"Listing packages: page={page}, per_page={per_page}, sort={sort}")

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
    logger.info(f"Searching packages: q='{q}', type={type}, limit={limit}")

    # TODO: Implement actual search
    return PackageSearchResponse(
        results=[],
        total=0,
        query=q,
    )


################################################################################
#                                                                              #
# SCOPED PACKAGE ENDPOINTS (must be defined BEFORE unscoped)                   #
#                                                                              #
################################################################################


@router.get("/@{scope}/{name}", response_model=PackageResponse)
async def get_scoped_package(scope: str, name: str) -> PackageResponse:
    """Get scoped package details."""
    _validate_scope(scope)
    _validate_name(name)
    return await _get_package_impl(scope, name)


@router.get("/@{scope}/{name}/{version}")
async def get_scoped_package_version(
    scope: str, name: str, version: str
) -> dict[str, object]:
    """Get specific scoped package version details."""
    _validate_scope(scope)
    _validate_name(name)
    return await _get_version_impl(scope, name, version)


@router.get("/@{scope}/{name}/{version}/download")
async def download_scoped_package(
    scope: str, name: str, version: str
) -> dict[str, str]:
    """Get download URL for scoped package."""
    _validate_scope(scope)
    _validate_name(name)
    return await _download_impl(scope, name, version)


@router.delete("/@{scope}/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def unpublish_scoped_package(scope: str, name: str) -> None:
    """Unpublish a scoped package (admin only)."""
    _validate_scope(scope)
    _validate_name(name)
    await _delete_package_impl(scope, name)


@router.delete(
    "/@{scope}/{name}/{version}", status_code=status.HTTP_204_NO_CONTENT
)
async def unpublish_scoped_version(
    scope: str, name: str, version: str
) -> None:
    """Unpublish a specific scoped version."""
    _validate_scope(scope)
    _validate_name(name)
    await _delete_version_impl(scope, name, version)


################################################################################
#                                                                              #
# UNSCOPED PACKAGE ENDPOINTS                                                   #
#                                                                              #
################################################################################


@router.get("/{name}", response_model=PackageResponse)
async def get_package(name: str) -> PackageResponse:
    """Get unscoped package details."""
    _validate_name(name)
    return await _get_package_impl("", name)


@router.get("/{name}/{version}")
async def get_package_version(
    name: str, version: str
) -> dict[str, object]:
    """Get specific unscoped package version details."""
    _validate_name(name)
    return await _get_version_impl("", name, version)


@router.get("/{name}/{version}/download")
async def download_package(name: str, version: str) -> dict[str, str]:
    """Get download URL for unscoped package."""
    _validate_name(name)
    return await _download_impl("", name, version)


################################################################################
#                                                                              #
# PUBLISH ENDPOINT                                                             #
#                                                                              #
################################################################################


@router.post("", response_model=PublishResponse, status_code=status.HTTP_201_CREATED)
async def publish_package(file: UploadFile) -> PublishResponse:
    """Publish a new package or version.

    The package name and scope are read from the uploaded manifest inside
    the archive.  Both scoped and unscoped packages are accepted.
    """
    logger.info("Publishing package")

    # TODO: Implement package upload and processing
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided",
        )

    return PublishResponse(
        name="example-package",
        scope="",
        version="1.0.0",
        message="Package published successfully",
    )


################################################################################
#                                                                              #
# SCOPED DIST-TAG ENDPOINTS                                                    #
#                                                                              #
################################################################################


class DistTagSetRequest(BaseModel):
    """Request body for setting a dist-tag."""

    version: str


class DistTagResponse(BaseModel):
    """Response for a single dist-tag operation."""

    package: str
    tag: str
    version: str


class DistTagListResponse(BaseModel):
    """Response listing all dist-tags for a package."""

    package: str
    tags: dict[str, str]


@router.get("/@{scope}/{name}/tags", response_model=DistTagListResponse)
async def list_scoped_dist_tags(
    scope: str, name: str
) -> DistTagListResponse:
    """List all dist-tags for a scoped package."""
    _validate_scope(scope)
    _validate_name(name)
    full_name = format_package_name(scope, name)
    logger.info(f"Listing dist-tags: package='{full_name}'")

    # TODO: Implement dist-tag listing from database
    return DistTagListResponse(package=full_name, tags={})


@router.put("/@{scope}/{name}/tags/{tag}", response_model=DistTagResponse)
async def set_scoped_dist_tag(
    scope: str, name: str, tag: str, body: DistTagSetRequest
) -> DistTagResponse:
    """Set a dist-tag for a scoped package (owner only)."""
    _validate_scope(scope)
    _validate_name(name)
    full_name = format_package_name(scope, name)
    logger.info(
        f"Setting dist-tag: package='{full_name}', "
        f"tag='{tag}', version='{body.version}'"
    )

    # TODO: Implement dist-tag set in database
    return DistTagResponse(
        package=full_name, tag=tag, version=body.version
    )


@router.delete(
    "/@{scope}/{name}/tags/{tag}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_scoped_dist_tag(
    scope: str, name: str, tag: str
) -> None:
    """Remove a dist-tag from a scoped package (owner only)."""
    _validate_scope(scope)
    _validate_name(name)
    full_name = format_package_name(scope, name)
    logger.info(f"Removing dist-tag: package='{full_name}', tag='{tag}'")

    # TODO: Implement dist-tag removal in database


################################################################################
#                                                                              #
# SCOPED APPROVAL ENDPOINTS                                                    #
#                                                                              #
################################################################################


class ApprovalRequest(BaseModel):
    """Request body for approving or rejecting a version."""

    status: str  # "approved" or "rejected"
    comment: str | None = None


class ApprovalResponse(BaseModel):
    """Response for a single approval action."""

    version_id: str
    approver: str
    status: str
    comment: str | None
    created_at: str


class ApprovalListResponse(BaseModel):
    """Response listing all approvals for a version."""

    package: str
    version: str
    approval_status: str
    approvals: list[ApprovalResponse]


@router.post(
    "/@{scope}/{name}/{version}/approve",
    response_model=ApprovalResponse,
    status_code=status.HTTP_201_CREATED,
)
async def approve_scoped_version(
    scope: str, name: str, version: str, body: ApprovalRequest
) -> ApprovalResponse:
    """Approve or reject a scoped package version."""
    _validate_scope(scope)
    _validate_name(name)
    full_name = format_package_name(scope, name)
    logger.info(
        f"Approving version: package='{full_name}', "
        f"version='{version}', status='{body.status}'"
    )

    # TODO: Implement approval logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Approval workflow not yet implemented",
    )


@router.get(
    "/@{scope}/{name}/{version}/approvals",
    response_model=ApprovalListResponse,
)
async def list_scoped_version_approvals(
    scope: str, name: str, version: str
) -> ApprovalListResponse:
    """List approvals for a scoped package version."""
    _validate_scope(scope)
    _validate_name(name)
    full_name = format_package_name(scope, name)
    logger.info(
        f"Listing approvals: package='{full_name}', version='{version}'"
    )

    # TODO: Implement approval listing
    return ApprovalListResponse(
        package=full_name,
        version=version,
        approval_status="none",
        approvals=[],
    )


################################################################################
#                                                                              #
# SCOPED EVAL RESULTS ENDPOINTS                                                #
#                                                                              #
################################################################################


class EvalResultRequest(BaseModel):
    """Request body for uploading eval results."""

    eval_name: str
    status: str  # "passed", "failed", "error"
    metrics: dict[str, object] | None = None
    run_at: str
    runner_identity: str | None = None
    environment: dict[str, object] | None = None


class EvalResultResponse(BaseModel):
    """Response for a single eval result."""

    id: str
    eval_name: str
    status: str
    metrics: dict[str, object] | None
    run_at: str


class EvalResultListResponse(BaseModel):
    """Response listing all eval results for a version."""

    package: str
    version: str
    eval_results: list[EvalResultResponse]


@router.post(
    "/@{scope}/{name}/{version}/eval-results",
    response_model=EvalResultResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_scoped_eval_results(
    scope: str, name: str, version: str, body: EvalResultRequest
) -> EvalResultResponse:
    """Upload eval results for a scoped package version (owner only)."""
    _validate_scope(scope)
    _validate_name(name)
    full_name = format_package_name(scope, name)
    logger.info(
        f"Uploading eval results: package='{full_name}', "
        f"version='{version}', eval='{body.eval_name}'"
    )

    # TODO: Implement eval result storage
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Eval results upload not yet implemented",
    )


@router.get(
    "/@{scope}/{name}/{version}/eval-results",
    response_model=EvalResultListResponse,
)
async def get_scoped_eval_results(
    scope: str, name: str, version: str
) -> EvalResultListResponse:
    """Get eval results for a scoped package version."""
    _validate_scope(scope)
    _validate_name(name)
    full_name = format_package_name(scope, name)
    logger.info(
        f"Getting eval results: package='{full_name}', version='{version}'"
    )

    # TODO: Implement eval result retrieval
    return EvalResultListResponse(
        package=full_name, version=version, eval_results=[]
    )


################################################################################
#                                                                              #
# UNSCOPED DIST-TAG ENDPOINTS                                                  #
#                                                                              #
################################################################################


@router.get("/{name}/tags", response_model=DistTagListResponse)
async def list_dist_tags(name: str) -> DistTagListResponse:
    """List all dist-tags for an unscoped package."""
    _validate_name(name)
    logger.info(f"Listing dist-tags: package='{name}'")

    # TODO: Implement dist-tag listing
    return DistTagListResponse(package=name, tags={})


@router.put("/{name}/tags/{tag}", response_model=DistTagResponse)
async def set_dist_tag(
    name: str, tag: str, body: DistTagSetRequest
) -> DistTagResponse:
    """Set a dist-tag for an unscoped package (owner only)."""
    _validate_name(name)
    logger.info(
        f"Setting dist-tag: package='{name}', "
        f"tag='{tag}', version='{body.version}'"
    )

    # TODO: Implement dist-tag set
    return DistTagResponse(package=name, tag=tag, version=body.version)


@router.delete(
    "/{name}/tags/{tag}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_dist_tag(name: str, tag: str) -> None:
    """Remove a dist-tag from an unscoped package (owner only)."""
    _validate_name(name)
    logger.info(f"Removing dist-tag: package='{name}', tag='{tag}'")

    # TODO: Implement dist-tag removal


################################################################################
#                                                                              #
# UNSCOPED APPROVAL ENDPOINTS                                                  #
#                                                                              #
################################################################################


@router.post(
    "/{name}/{version}/approve",
    response_model=ApprovalResponse,
    status_code=status.HTTP_201_CREATED,
)
async def approve_version(
    name: str, version: str, body: ApprovalRequest
) -> ApprovalResponse:
    """Approve or reject an unscoped package version."""
    _validate_name(name)
    logger.info(
        f"Approving version: package='{name}', "
        f"version='{version}', status='{body.status}'"
    )

    # TODO: Implement approval logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Approval workflow not yet implemented",
    )


@router.get(
    "/{name}/{version}/approvals",
    response_model=ApprovalListResponse,
)
async def list_version_approvals(
    name: str, version: str
) -> ApprovalListResponse:
    """List approvals for an unscoped package version."""
    _validate_name(name)
    logger.info(
        f"Listing approvals: package='{name}', version='{version}'"
    )

    # TODO: Implement approval listing
    return ApprovalListResponse(
        package=name,
        version=version,
        approval_status="none",
        approvals=[],
    )


################################################################################
#                                                                              #
# UNSCOPED EVAL RESULTS ENDPOINTS                                              #
#                                                                              #
################################################################################


@router.post(
    "/{name}/{version}/eval-results",
    response_model=EvalResultResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_eval_results(
    name: str, version: str, body: EvalResultRequest
) -> EvalResultResponse:
    """Upload eval results for an unscoped package version (owner only)."""
    _validate_name(name)
    logger.info(
        f"Uploading eval results: package='{name}', "
        f"version='{version}', eval='{body.eval_name}'"
    )

    # TODO: Implement eval result storage
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Eval results upload not yet implemented",
    )


@router.get(
    "/{name}/{version}/eval-results",
    response_model=EvalResultListResponse,
)
async def get_eval_results(
    name: str, version: str
) -> EvalResultListResponse:
    """Get eval results for an unscoped package version."""
    _validate_name(name)
    logger.info(
        f"Getting eval results: package='{name}', version='{version}'"
    )

    # TODO: Implement eval result retrieval
    return EvalResultListResponse(
        package=name, version=version, eval_results=[]
    )


################################################################################
#                                                                              #
# UNSCOPED DELETE ENDPOINTS                                                    #
#                                                                              #
################################################################################


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def unpublish_package(name: str) -> None:
    """Unpublish an unscoped package (admin only)."""
    _validate_name(name)
    await _delete_package_impl("", name)


@router.delete("/{name}/{version}", status_code=status.HTTP_204_NO_CONTENT)
async def unpublish_version(name: str, version: str) -> None:
    """Unpublish a specific unscoped version."""
    _validate_name(name)
    await _delete_version_impl("", name, version)
