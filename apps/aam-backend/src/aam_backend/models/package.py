"""Package model."""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import logging

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aam_backend.models.base import Base, TimestampMixin, UUIDMixin

################################################################################
#                                                                              #
# LOGGING                                                                      #
#                                                                              #
################################################################################

# Initialize logger for this module
logger = logging.getLogger(__name__)

################################################################################
#                                                                              #
# MODELS                                                                       #
#                                                                              #
################################################################################


class Package(Base, UUIDMixin, TimestampMixin):
    """Package model.

    Supports both unscoped packages (e.g., ``my-package``) and scoped packages
    (e.g., ``@author/my-package``).  The ``scope`` column stores the scope name
    without the leading ``@`` (empty string for unscoped packages).  Uniqueness
    is enforced on the composite ``(scope, name)`` pair.
    """

    __tablename__ = "packages"

    # -----
    # Table-level constraints
    # -----
    # Composite unique constraint replaces the old unique=True on name.
    # Using empty string (not NULL) for unscoped packages avoids the
    # PostgreSQL NULL-uniqueness problem.
    __table_args__ = (
        UniqueConstraint("scope", "name", name="uq_packages_scope_name"),
    )

    # -----
    # Scope column — empty string for unscoped, e.g. "author" for @author/pkg
    # -----
    scope: Mapped[str] = mapped_column(
        String(64), nullable=False, default="", index=True
    )

    # -----
    # Name column — package name without scope prefix
    # -----
    name: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    package_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="agent"
    )

    # Metadata
    homepage: Mapped[str | None] = mapped_column(String(500), nullable=True)
    repository: Mapped[str | None] = mapped_column(String(500), nullable=True)
    license: Mapped[str | None] = mapped_column(String(50), nullable=True)
    keywords: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(50)), nullable=True
    )

    # Stats
    downloads: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    # Author relationship
    author_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    author: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User",
        back_populates="packages",
    )

    # Versions relationship
    versions: Mapped[list["PackageVersion"]] = relationship(
        "PackageVersion",
        back_populates="package",
        lazy="selectin",
        order_by="desc(PackageVersion.created_at)",
    )

    @property
    def full_name(self) -> str:
        """Return the full package name including scope prefix.

        Returns ``@scope/name`` for scoped packages and ``name`` for unscoped.
        """
        if self.scope:
            return f"@{self.scope}/{self.name}"
        return self.name

    def __repr__(self) -> str:
        """String representation."""
        return f"<Package {self.full_name}>"


class PackageVersion(Base, UUIDMixin, TimestampMixin):
    """Package version model."""

    __tablename__ = "package_versions"

    version: Mapped[str] = mapped_column(String(50), nullable=False)

    # Content
    readme: Mapped[str | None] = mapped_column(Text, nullable=True)
    manifest: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)

    # Storage
    tarball_url: Mapped[str] = mapped_column(String(500), nullable=False)
    tarball_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    size: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Governance — approval workflow status
    approval_status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="none"
    )  # "none", "pending", "approved", "rejected"

    # Stats
    downloads: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    # Package relationship
    package_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("packages.id", ondelete="CASCADE"),
        nullable=False,
    )
    package: Mapped["Package"] = relationship(
        "Package",
        back_populates="versions",
    )

    # Relationships to governance / quality models
    approvals: Mapped[list["VersionApproval"]] = relationship(
        "VersionApproval",
        back_populates="version",
        lazy="selectin",
    )
    eval_results: Mapped[list["EvalResult"]] = relationship(
        "EvalResult",
        back_populates="version",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<PackageVersion {self.package.full_name}@{self.version}>"


################################################################################
#                                                                              #
# DIST-TAG MODEL                                                               #
#                                                                              #
################################################################################


class DistTag(Base, UUIDMixin, TimestampMixin):
    """Named alias pointing a tag string to a specific package version.

    Examples: ``latest``, ``stable``, ``bank-approved``.

    Tags are stored per-package and must be unique within a package
    (enforced by ``uq_dist_tags_package_tag``).
    """

    __tablename__ = "dist_tags"

    # -----
    # Table-level constraints
    # -----
    __table_args__ = (
        UniqueConstraint(
            "package_id", "tag", name="uq_dist_tags_package_tag"
        ),
    )

    # -----
    # Columns
    # -----
    package_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("packages.id", ondelete="CASCADE"),
        nullable=False,
    )
    tag: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # e.g., "latest", "stable", "bank-approved"
    version_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("package_versions.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    package: Mapped["Package"] = relationship("Package")
    version: Mapped["PackageVersion"] = relationship("PackageVersion")

    def __repr__(self) -> str:
        """String representation."""
        return f"<DistTag {self.tag}={self.version_id}>"


################################################################################
#                                                                              #
# AUDIT LOG MODEL                                                              #
#                                                                              #
################################################################################


class AuditLogEntry(Base, UUIDMixin):
    """Immutable, append-only audit log entry.

    Every mutation on the registry (publish, yank, tag change, ownership
    transfer) is recorded here.  Entries are never updated or deleted.
    """

    __tablename__ = "audit_log"

    # -----
    # Columns
    # -----
    event: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # e.g., "package.publish", "version.yank", "tag.set"
    actor_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=True,
    )
    package_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("packages.id", ondelete="SET NULL"),
        nullable=True,
    )
    version_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("package_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    metadata_json: Mapped[dict[str, object] | None] = mapped_column(
        JSONB, nullable=True
    )
    timestamp: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<AuditLogEntry {self.event} at {self.timestamp}>"


################################################################################
#                                                                              #
# VERSION APPROVAL MODEL                                                       #
#                                                                              #
################################################################################


class VersionApproval(Base, UUIDMixin, TimestampMixin):
    """Records an approval or rejection of a package version by an approver."""

    __tablename__ = "version_approvals"

    # -----
    # Columns
    # -----
    version_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("package_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    approver_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False
    )  # "approved", "rejected"
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    version: Mapped["PackageVersion"] = relationship(
        "PackageVersion",
        back_populates="approvals",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<VersionApproval {self.status} by {self.approver_id}>"


################################################################################
#                                                                              #
# EVAL RESULT MODEL                                                            #
#                                                                              #
################################################################################


class EvalResult(Base, UUIDMixin, TimestampMixin):
    """Stores the result of an evaluation run against a package version.

    Eval results include metrics (accuracy, latency, etc.) and are
    surfaced in ``aam info`` and ``aam search`` to help consumers judge
    package quality.
    """

    __tablename__ = "eval_results"

    # -----
    # Columns
    # -----
    version_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("package_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    eval_name: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # e.g., "accuracy-eval"
    status: Mapped[str] = mapped_column(
        String(16), nullable=False
    )  # "passed", "failed", "error"
    metrics: Mapped[dict[str, object] | None] = mapped_column(
        JSONB, nullable=True
    )  # {"accuracy": 94.2, "latency_p95": 1200}
    run_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    runner_identity: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # who ran the eval
    environment: Mapped[dict[str, object] | None] = mapped_column(
        JSONB, nullable=True
    )  # model, runtime info

    # Relationships
    version: Mapped["PackageVersion"] = relationship(
        "PackageVersion",
        back_populates="eval_results",
    )
