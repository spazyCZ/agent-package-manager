"""Add governance and quality tables.

Revision ID: 002_add_governance_quality
Revises: 001_add_scope
Create Date: 2026-02-07

This migration adds tables and columns for:

1. ``dist_tags`` — named version aliases (e.g. latest, stable, bank-approved)
2. ``audit_log`` — immutable append-only audit trail for registry mutations
3. ``version_approvals`` — approval/rejection records for package versions
4. ``eval_results`` — evaluation run results with metrics
5. ``approval_status`` column on ``package_versions``
"""

################################################################################
#                                                                              #
# IMPORTS & DEPENDENCIES                                                       #
#                                                                              #
################################################################################

import sqlalchemy as sa
from alembic import op

################################################################################
#                                                                              #
# REVISION METADATA                                                            #
#                                                                              #
################################################################################

# revision identifiers, used by Alembic.
revision = "002_add_governance_quality"
down_revision = "001_add_scope"
branch_labels = None
depends_on = None

################################################################################
#                                                                              #
# MIGRATION OPERATIONS                                                         #
#                                                                              #
################################################################################


def upgrade() -> None:
    """Apply the migration — create governance and quality tables."""
    # -----
    # Step 1: Add approval_status column to package_versions
    # -----
    op.add_column(
        "package_versions",
        sa.Column(
            "approval_status",
            sa.String(16),
            nullable=False,
            server_default="none",
        ),
    )

    # -----
    # Step 2: Create dist_tags table
    # -----
    op.create_table(
        "dist_tags",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "package_id",
            sa.String(36),
            sa.ForeignKey("packages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tag", sa.String(32), nullable=False),
        sa.Column(
            "version_id",
            sa.String(36),
            sa.ForeignKey("package_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "package_id", "tag", name="uq_dist_tags_package_tag"
        ),
    )
    op.create_index("ix_dist_tags_package_id", "dist_tags", ["package_id"])

    # -----
    # Step 3: Create audit_log table (append-only)
    # -----
    op.create_table(
        "audit_log",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("event", sa.String(64), nullable=False),
        sa.Column(
            "actor_id",
            sa.String(36),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column(
            "package_id",
            sa.String(36),
            sa.ForeignKey("packages.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "version_id",
            sa.String(36),
            sa.ForeignKey("package_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("metadata_json", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_audit_log_event", "audit_log", ["event"])
    op.create_index("ix_audit_log_package_id", "audit_log", ["package_id"])
    op.create_index("ix_audit_log_timestamp", "audit_log", ["timestamp"])

    # -----
    # Step 4: Create version_approvals table
    # -----
    op.create_table(
        "version_approvals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "version_id",
            sa.String(36),
            sa.ForeignKey("package_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "approver_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("comment", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_version_approvals_version_id",
        "version_approvals",
        ["version_id"],
    )

    # -----
    # Step 5: Create eval_results table
    # -----
    op.create_table(
        "eval_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "version_id",
            sa.String(36),
            sa.ForeignKey("package_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("eval_name", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("metrics", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column("run_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("runner_identity", sa.String(255), nullable=True),
        sa.Column("environment", sa.dialects.postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_eval_results_version_id", "eval_results", ["version_id"]
    )


def downgrade() -> None:
    """Reverse the migration — drop governance and quality tables."""
    # -----
    # Step 1: Drop eval_results table
    # -----
    op.drop_index("ix_eval_results_version_id", "eval_results")
    op.drop_table("eval_results")

    # -----
    # Step 2: Drop version_approvals table
    # -----
    op.drop_index("ix_version_approvals_version_id", "version_approvals")
    op.drop_table("version_approvals")

    # -----
    # Step 3: Drop audit_log table
    # -----
    op.drop_index("ix_audit_log_timestamp", "audit_log")
    op.drop_index("ix_audit_log_package_id", "audit_log")
    op.drop_index("ix_audit_log_event", "audit_log")
    op.drop_table("audit_log")

    # -----
    # Step 4: Drop dist_tags table
    # -----
    op.drop_index("ix_dist_tags_package_id", "dist_tags")
    op.drop_table("dist_tags")

    # -----
    # Step 5: Remove approval_status from package_versions
    # -----
    op.drop_column("package_versions", "approval_status")
