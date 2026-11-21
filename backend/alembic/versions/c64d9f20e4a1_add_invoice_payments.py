"""add invoice payments

Revision ID: c64d9f20e4a1
Revises: b8f43c12ad90
Create Date: 2026-11-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c64d9f20e4a1"
down_revision: str | None = "b8f43c12ad90"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_id", sa.Integer(), sa.ForeignKey("businesses.id"), nullable=False),
        sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("method", sa.String(20), nullable=False),
        sa.Column("reference", sa.String(100), nullable=True),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="RECORDED"),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("voided_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("void_reason", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("amount > 0", name="ck_payments_amount_positive"),
        sa.CheckConstraint("status IN ('RECORDED', 'VOIDED')", name="ck_payments_status"),
        sa.CheckConstraint("method IN ('TRANSFER', 'CASH', 'CARD', 'OTHER')", name="ck_payments_method"),
    )
    op.create_index("ix_payments_business_id", "payments", ["business_id"])
    op.create_index("ix_payments_invoice_id", "payments", ["invoice_id"])
    op.create_index(
        "ix_payments_business_invoice_status", "payments",
        ["business_id", "invoice_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_payments_business_invoice_status", table_name="payments")
    op.drop_index("ix_payments_invoice_id", table_name="payments")
    op.drop_index("ix_payments_business_id", table_name="payments")
    op.drop_table("payments")
