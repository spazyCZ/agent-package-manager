"""Add scope column to packages table for scoped package support.

Revision ID: 001_add_scope
Revises:
Create Date: 2026-02-07

This migration adds support for ``@scope/package-name`` scoped packages:

1. Adds a ``scope`` column (NOT NULL, default '') to the ``packages`` table.
2. Drops the old unique index on ``name``.
3. Adds a composite unique constraint on ``(scope, name)``.
4. Increases ``dependency_name`` VARCHAR from 64 to 130 in ``dependencies``
   table to accommodate scoped names like ``@scope/name``.
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
revision = "001_add_scope"
down_revision = None
branch_labels = None
depends_on = None

################################################################################
#                                                                              #
# MIGRATION OPERATIONS                                                         #
#                                                                              #
################################################################################


def upgrade() -> None:
    """Apply the migration — add scope column and update constraints."""
    # -----
    # Step 1: Add the scope column with a default of empty string
    # -----
    op.add_column(
        "packages",
        sa.Column(
            "scope",
            sa.String(64),
            nullable=False,
            server_default="",
        ),
    )

    # -----
    # Step 2: Create an index on the scope column for faster lookups
    # -----
    op.create_index("ix_packages_scope", "packages", ["scope"])

    # -----
    # Step 3: Drop the old unique constraint on name only
    # -----
    # The old model had unique=True on the name column.  We need to drop it
    # and replace it with a composite unique on (scope, name).
    op.drop_constraint("packages_name_key", "packages", type_="unique")

    # -----
    # Step 4: Add composite unique constraint on (scope, name)
    # -----
    op.create_unique_constraint(
        "uq_packages_scope_name",
        "packages",
        ["scope", "name"],
    )

    # -----
    # Step 5: Alter name column from String(100) to String(64)
    # -----
    # Now that scope is separate, the name column only holds the name part.
    op.alter_column(
        "packages",
        "name",
        type_=sa.String(64),
        existing_type=sa.String(100),
        existing_nullable=False,
    )

    # -----
    # Step 6: Increase dependency_name VARCHAR to fit scoped names
    # -----
    # Only apply if the dependencies table exists (it is defined in the SQL
    # spec but may not exist yet in all environments).
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "dependencies" in inspector.get_table_names():
        op.alter_column(
            "dependencies",
            "dependency_name",
            type_=sa.String(130),
            existing_type=sa.String(64),
            existing_nullable=False,
        )


def downgrade() -> None:
    """Reverse the migration — remove scope column and restore constraints."""
    # -----
    # Step 1: Revert dependency_name VARCHAR
    # -----
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "dependencies" in inspector.get_table_names():
        op.alter_column(
            "dependencies",
            "dependency_name",
            type_=sa.String(64),
            existing_type=sa.String(130),
            existing_nullable=False,
        )

    # -----
    # Step 2: Revert name column back to String(100)
    # -----
    op.alter_column(
        "packages",
        "name",
        type_=sa.String(100),
        existing_type=sa.String(64),
        existing_nullable=False,
    )

    # -----
    # Step 3: Drop composite unique constraint
    # -----
    op.drop_constraint("uq_packages_scope_name", "packages", type_="unique")

    # -----
    # Step 4: Restore original unique constraint on name only
    # -----
    op.create_unique_constraint("packages_name_key", "packages", ["name"])

    # -----
    # Step 5: Drop the scope index
    # -----
    op.drop_index("ix_packages_scope", "packages")

    # -----
    # Step 6: Drop the scope column
    # -----
    op.drop_column("packages", "scope")
