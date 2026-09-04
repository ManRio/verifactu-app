"""enforce case insensitive user email uniqueness

Revision ID: 666e0bbbf372
Revises: a23de07e7fb2
Create Date: 2026-09-04 12:25:05.776258

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "666e0bbbf372"
down_revision: str | Sequence[str] | None = "a23de07e7fb2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    op.drop_index(
        "ix_users_email",
        table_name="users",
    )

    op.create_index(
        "ix_users_email",
        "users",
        ["email"],
        unique=False,
    )

    op.create_index(
        "uq_users_email_lower",
        "users",
        [sa.text("lower(email)")],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        "uq_users_email_lower",
        table_name="users",
    )

    op.drop_index(
        "ix_users_email",
        table_name="users",
    )

    op.create_index(
        "ix_users_email",
        "users",
        ["email"],
        unique=True,
    )