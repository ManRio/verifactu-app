"""add demo subscriptions

Revision ID: b8f43c12ad90
Revises: 36344f288a54
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b8f43c12ad90"
down_revision: Union[str, Sequence[str], None] = "36344f288a54"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("business_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), server_default="PENDING", nullable=False),
        sa.Column("plan_code", sa.String(20), nullable=True),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"]),
    )
    op.create_index("ix_subscriptions_business_id", "subscriptions", ["business_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_subscriptions_business_id", table_name="subscriptions")
    op.drop_table("subscriptions")
