"""Initial migration with users, devices, backup_codes tables

Revision ID: 001_initial_migration
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001_initial_migration"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("tfa_enabled", sa.Boolean(), server_default="false"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    # Create devices table
    op.create_table(
        "devices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("device_name", sa.String(255), nullable=False),
        sa.Column("device_type", sa.String(50), nullable=False),
        sa.Column("totp_secret", sa.String(64), nullable=True),
        sa.Column("fcm_token", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_devices_id"), "devices", ["id"], unique=False)
    op.create_index("ix_devices_user_id", "devices", ["user_id"], unique=False)

    # Create backup_codes table
    op.create_table(
        "backup_codes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("code_hash", sa.String(255), nullable=False),
        sa.Column("is_used", sa.Boolean(), server_default="false"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
        ),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_backup_codes_id"), "backup_codes", ["id"], unique=False)

    # Create pending_2fa_sessions table
    op.create_table(
        "pending_2fa_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("temp_token", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_pending_2fa_sessions_id"), "pending_2fa_sessions", ["id"], unique=False
    )
    op.create_index(
        "ix_pending_2fa_sessions_temp_token",
        "pending_2fa_sessions",
        ["temp_token"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("pending_2fa_sessions")
    op.drop_table("backup_codes")
    op.drop_table("devices")
    op.drop_table("users")
