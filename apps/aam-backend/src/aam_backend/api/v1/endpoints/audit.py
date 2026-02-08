"""Audit log endpoints.

Provides read-only access to the immutable audit log for registry mutations.
Supports querying by package, event type, actor, and date range.
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging
from datetime import datetime

from fastapi import APIRouter, Query
from pydantic import BaseModel

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


class AuditLogEntryResponse(BaseModel):
    """Single audit log entry response."""

    id: str
    event: str
    actor: str | None
    package: str | None
    version: str | None
    timestamp: str
    metadata: dict[str, object] | None


class AuditLogListResponse(BaseModel):
    """Paginated audit log response."""

    entries: list[AuditLogEntryResponse]
    total: int
    page: int
    pages: int


################################################################################
#                                                                              #
# GLOBAL AUDIT LOG ENDPOINT                                                    #
#                                                                              #
################################################################################


@router.get("", response_model=AuditLogListResponse)
async def query_audit_log(
    package: str | None = Query(default=None, description="Filter by package name"),
    event: str | None = Query(default=None, description="Filter by event type"),
    actor: str | None = Query(default=None, description="Filter by actor username"),
    from_date: datetime | None = Query(
        default=None, alias="from", description="Start of date range (ISO 8601)"
    ),
    to_date: datetime | None = Query(
        default=None, alias="to", description="End of date range (ISO 8601)"
    ),
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=50, ge=1, le=200, description="Results per page"),
) -> AuditLogListResponse:
    """Query the global audit log.

    Requires admin authentication. Supports filtering by package name,
    event type, actor, and date range.

    Args:
        package: Filter by package name (full name including scope).
        event: Filter by event type (e.g. ``package.publish``, ``tag.set``).
        actor: Filter by actor username.
        from_date: Start of date range (ISO 8601).
        to_date: End of date range (ISO 8601).
        page: Page number (1-indexed).
        limit: Number of results per page (max 200).

    Returns:
        Paginated list of audit log entries.
    """
    logger.info(
        f"Querying audit log: package={package}, event={event}, "
        f"actor={actor}, from={from_date}, to={to_date}, "
        f"page={page}, limit={limit}"
    )

    # TODO: Implement actual database query with filters
    return AuditLogListResponse(
        entries=[],
        total=0,
        page=page,
        pages=0,
    )
