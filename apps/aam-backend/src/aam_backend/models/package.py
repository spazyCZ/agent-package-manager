"""Package model."""

from sqlalchemy import BigInteger, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aam_backend.models.base import Base, TimestampMixin, UUIDMixin


class Package(Base, UUIDMixin, TimestampMixin):
    """Package model."""

    __tablename__ = "packages"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    package_type: Mapped[str] = mapped_column(String(20), nullable=False, default="agent")

    # Metadata
    homepage: Mapped[str | None] = mapped_column(String(500), nullable=True)
    repository: Mapped[str | None] = mapped_column(String(500), nullable=True)
    license: Mapped[str | None] = mapped_column(String(50), nullable=True)
    keywords: Mapped[list[str] | None] = mapped_column(ARRAY(String(50)), nullable=True)

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

    def __repr__(self) -> str:
        """String representation."""
        return f"<Package {self.name}>"


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

    def __repr__(self) -> str:
        """String representation."""
        return f"<PackageVersion {self.package.name}@{self.version}>"
