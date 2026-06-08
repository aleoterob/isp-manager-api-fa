"""initial schema

Revision ID: 202606080000
Revises:
Create Date: 2026-06-08 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "202606080000"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


role_enum = sa.Enum("ADMIN", "SUPERVISOR", "INSTALLER", name="Role")
order_type_enum = sa.Enum(
    "INSTALLATION", "RELOCATION", "REPAIR", "UNINSTALL", "UPGRADE", name="OrderType"
)
order_status_enum = sa.Enum(
    "PENDING", "IN_PROGRESS", "COMPLETED", "CANCELLED", name="OrderStatus"
)
movement_type_enum = sa.Enum("IN", "OUT", "ADJUST", name="MovementType")
notification_type_enum = sa.Enum(
    "ORDER_ASSIGNED", "ORDER_UPDATED", "LOW_STOCK", "GENERAL", name="NotificationType"
)
refresh_session_status_enum = sa.Enum(
    "ACTIVE", "REPLACED", "REVOKED", name="RefreshSessionStatus"
)


def upgrade() -> None:
    bind = op.get_bind()
    for enum in [
        role_enum,
        order_type_enum,
        order_status_enum,
        movement_type_enum,
        notification_type_enum,
        refresh_session_status_enum,
    ]:
        enum.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("role", role_enum, server_default="INSTALLER", nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("lastLoginAt", sa.DateTime(), nullable=True),
        sa.Column("createdAt", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updatedAt", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("users_email_key", "users", ["email"], unique=True)

    op.create_table(
        "customers",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("address", sa.String(), nullable=True),
        sa.Column("city", sa.String(), nullable=True),
        sa.Column("province", sa.String(), nullable=True),
        sa.Column("zipCode", sa.String(), nullable=True),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lng", sa.Float(), nullable=True),
        sa.Column("createdAt", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updatedAt", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "equipment_categories",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("createdAt", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updatedAt", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "equipment_categories_name_key", "equipment_categories", ["name"], unique=True
    )

    op.create_table(
        "units",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("abbreviation", sa.String(), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("createdAt", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updatedAt", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("units_name_key", "units", ["name"], unique=True)

    op.create_table(
        "warehouses",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("address", sa.String(), nullable=True),
        sa.Column("city", sa.String(), nullable=True),
        sa.Column("province", sa.String(), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("createdAt", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updatedAt", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "equipment",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("categoryId", sa.String(), nullable=False),
        sa.Column("unitId", sa.String(), nullable=False),
        sa.Column("createdAt", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updatedAt", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["categoryId"], ["equipment_categories.id"]),
        sa.ForeignKeyConstraint(["unitId"], ["units.id"]),
    )

    op.create_table(
        "orders",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("type", order_type_enum, nullable=False),
        sa.Column("status", order_status_enum, server_default="PENDING", nullable=False),
        sa.Column("address", sa.String(), nullable=True),
        sa.Column("city", sa.String(), nullable=True),
        sa.Column("province", sa.String(), nullable=True),
        sa.Column("zipCode", sa.String(), nullable=True),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lng", sa.Float(), nullable=True),
        sa.Column("scheduledAt", sa.DateTime(), nullable=True),
        sa.Column("installerId", sa.String(), nullable=True),
        sa.Column("customerId", sa.String(), nullable=True),
        sa.Column("createdAt", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updatedAt", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["installerId"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["customerId"], ["customers.id"], ondelete="SET NULL"),
    )

    op.create_table(
        "refresh_sessions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("userId", sa.String(), nullable=False),
        sa.Column("tokenHash", sa.String(), nullable=False),
        sa.Column("familyId", sa.String(), nullable=False),
        sa.Column(
            "status",
            refresh_session_status_enum,
            server_default="ACTIVE",
            nullable=False,
        ),
        sa.Column("expiresAt", sa.DateTime(), nullable=False),
        sa.Column("createdAt", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["userId"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("refresh_sessions_tokenHash_key", "refresh_sessions", ["tokenHash"], unique=True)
    op.create_index("refresh_sessions_familyId_idx", "refresh_sessions", ["familyId"])
    op.create_index(
        "refresh_sessions_userId_familyId_idx",
        "refresh_sessions",
        ["userId", "familyId"],
    )

    op.create_table(
        "warehouse_stock",
        sa.Column("warehouseId", sa.String(), nullable=False),
        sa.Column("equipmentId", sa.String(), nullable=False),
        sa.Column("stock", sa.Integer(), server_default="0", nullable=False),
        sa.Column("minStock", sa.Integer(), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(["warehouseId"], ["warehouses.id"]),
        sa.ForeignKeyConstraint(["equipmentId"], ["equipment.id"]),
        sa.PrimaryKeyConstraint("warehouseId", "equipmentId"),
    )

    op.create_table(
        "order_equipment",
        sa.Column("orderId", sa.String(), nullable=False),
        sa.Column("equipmentId", sa.String(), nullable=False),
        sa.Column("warehouseId", sa.String(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["orderId"], ["orders.id"]),
        sa.ForeignKeyConstraint(["equipmentId"], ["equipment.id"]),
        sa.ForeignKeyConstraint(["warehouseId"], ["warehouses.id"]),
        sa.PrimaryKeyConstraint("orderId", "equipmentId"),
    )

    op.create_table(
        "stock_movements",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("equipmentId", sa.String(), nullable=False),
        sa.Column("warehouseId", sa.String(), nullable=False),
        sa.Column("userId", sa.String(), nullable=False),
        sa.Column("type", movement_type_enum, nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("note", sa.String(), nullable=True),
        sa.Column("createdAt", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["equipmentId"], ["equipment.id"]),
        sa.ForeignKeyConstraint(["warehouseId"], ["warehouses.id"]),
        sa.ForeignKeyConstraint(["userId"], ["users.id"]),
    )

    op.create_table(
        "order_notes",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("orderId", sa.String(), nullable=False),
        sa.Column("userId", sa.String(), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("createdAt", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["orderId"], ["orders.id"]),
        sa.ForeignKeyConstraint(["userId"], ["users.id"]),
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("userId", sa.String(), nullable=False),
        sa.Column(
            "type", notification_type_enum, server_default="GENERAL", nullable=False
        ),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("message", sa.String(), nullable=False),
        sa.Column("read", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("createdAt", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["userId"], ["users.id"]),
    )


def downgrade() -> None:
    for table in [
        "notifications",
        "order_notes",
        "stock_movements",
        "order_equipment",
        "warehouse_stock",
        "refresh_sessions",
        "orders",
        "equipment",
        "warehouses",
        "units",
        "equipment_categories",
        "customers",
        "users",
    ]:
        op.drop_table(table)

    bind = op.get_bind()
    for enum in [
        refresh_session_status_enum,
        notification_type_enum,
        movement_type_enum,
        order_status_enum,
        order_type_enum,
        role_enum,
    ]:
        enum.drop(bind, checkfirst=True)
