"""Roles por empresa y verificación de correo.

Revision ID: f7b20c81a611
Revises: c64d9f20e4a1
"""
from alembic import op
import sqlalchemy as sa

revision = "f7b20c81a611"
down_revision = "c64d9f20e4a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("role", sa.String(20), nullable=False, server_default="WORKER"))
    op.add_column("users", sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("users", sa.Column("must_set_password", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("users", sa.Column("verification_token_hash", sa.String(64), nullable=True))
    op.add_column("users", sa.Column("verification_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("verification_sent_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_users_verification_token_hash", "users", ["verification_token_hash"], unique=True)
    op.create_check_constraint("ck_users_role", "users", "role IN ('SUPERUSER', 'WORKER')")

    # Primer usuario histórico de cada empresa: superusuario. Resto: trabajador.
    op.execute("""
        WITH ranked AS (
            SELECT id, ROW_NUMBER() OVER (PARTITION BY business_id ORDER BY id) AS row_num
            FROM users
        )
        UPDATE users AS u SET role = 'SUPERUSER'
        FROM ranked AS r WHERE u.id = r.id AND r.row_num = 1
    """)


def downgrade() -> None:
    op.drop_constraint("ck_users_role", "users", type_="check")
    op.drop_index("ix_users_verification_token_hash", table_name="users")
    for name in ("verification_sent_at", "verification_expires_at", "verification_token_hash", "must_set_password", "email_verified", "role"):
        op.drop_column("users", name)
