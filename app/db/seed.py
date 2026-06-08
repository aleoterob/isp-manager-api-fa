from datetime import timedelta

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import SessionLocal, engine
from app.features.auth.models import RefreshSession
from app.features.auth.service import utc_now
from app.features.customers.models import Customer
from app.features.inventory.models import (
    Equipment,
    EquipmentCategory,
    MovementType,
    StockMovement,
    Unit,
    Warehouse,
    WarehouseStock,
)
from app.features.notifications.models import Notification, NotificationType
from app.features.orders.models import (
    Order,
    OrderEquipment,
    OrderNote,
    OrderStatus,
    OrderType,
)
from app.features.users.models import Role, User

SEED_PASSWORD = "SeedPass123!"


def assert_migrations_applied() -> None:
    inspector = inspect(engine)
    if "notifications" not in inspector.get_table_names():
        raise RuntimeError(
            "\n".join(
                [
                    "SQLAlchemy tables do not exist in this database.",
                    "From isp-manager-api-fa, apply migrations first:",
                    "  python -m alembic upgrade head",
                    "Then run the seed again.",
                ]
            )
        )


def wipe_dev_data(db: Session) -> None:
    for model in [
        RefreshSession,
        Notification,
        OrderNote,
        StockMovement,
        OrderEquipment,
        Order,
        WarehouseStock,
        Equipment,
        Warehouse,
        Customer,
        User,
        EquipmentCategory,
        Unit,
    ]:
        db.query(model).delete()
    db.commit()


def seed(db: Session) -> None:
    wipe_dev_data(db)
    password_hash = hash_password(SEED_PASSWORD)

    unit_unidad = Unit(name="Unidad", abbreviation="u", active=True)
    unit_metro = Unit(name="Metro", abbreviation="m", active=True)
    cat_router = EquipmentCategory(name="Router", active=True)
    cat_cable = EquipmentCategory(name="Cable", active=True)
    warehouse_central = Warehouse(
        name="Central Warehouse",
        address="100 Main Ave",
        city="Buenos Aires",
        province="CABA",
        active=True,
    )
    db.add_all([unit_unidad, unit_metro, cat_router, cat_cable, warehouse_central])
    db.flush()

    admin = User(
        name="Admin Demo",
        email="admin@isp.local",
        password=password_hash,
        phone="+54 11 1111-1111",
        role=Role.ADMIN,
        active=True,
    )
    supervisor = User(
        name="Supervisor Demo",
        email="supervisor@isp.local",
        password=password_hash,
        phone="+54 11 2222-2222",
        role=Role.SUPERVISOR,
        active=True,
    )
    installer = User(
        name="Instalador Demo",
        email="installer@isp.local",
        password=password_hash,
        phone="+54 11 3333-3333",
        role=Role.INSTALLER,
        active=True,
    )
    db.add_all([admin, supervisor, installer])
    db.flush()

    equip_router = Equipment(
        name="Router WiFi AX3000",
        categoryId=cat_router.id,
        unitId=unit_unidad.id,
    )
    equip_cable = Equipment(
        name="Cable FO drop 100m",
        categoryId=cat_cable.id,
        unitId=unit_metro.id,
    )
    db.add_all([equip_router, equip_cable])
    db.flush()

    db.add_all(
        [
            WarehouseStock(
                warehouseId=warehouse_central.id,
                equipmentId=equip_router.id,
                stock=25,
                minStock=5,
            ),
            WarehouseStock(
                warehouseId=warehouse_central.id,
                equipmentId=equip_cable.id,
                stock=120,
                minStock=20,
            ),
        ]
    )

    customer = Customer(
        name="Residential Customer Inc",
        email="contact@customer.example",
        phone="+54 11 4444-4444",
        address="Fake Street 123",
        city="La Plata",
        province="Buenos Aires",
        zipCode="1900",
    )
    db.add(customer)
    db.flush()

    order = Order(
        title="FTTH installation - Residential Customer Inc",
        description="New 300 Mbps service",
        type=OrderType.INSTALLATION,
        status=OrderStatus.IN_PROGRESS,
        address="Fake Street 123",
        city="La Plata",
        province="Buenos Aires",
        installerId=installer.id,
        customerId=customer.id,
        scheduledAt=utc_now() + timedelta(days=1),
    )
    db.add(order)
    db.flush()

    db.add_all(
        [
            OrderEquipment(
                orderId=order.id,
                equipmentId=equip_router.id,
                warehouseId=warehouse_central.id,
                quantity=1,
            ),
            OrderEquipment(
                orderId=order.id,
                equipmentId=equip_cable.id,
                warehouseId=warehouse_central.id,
                quantity=30,
            ),
            OrderNote(
                orderId=order.id,
                userId=installer.id,
                content=(
                    "Customer verified on site. "
                    "Conduit is ready for fiber routing."
                ),
            ),
            StockMovement(
                equipmentId=equip_router.id,
                warehouseId=warehouse_central.id,
                userId=admin.id,
                type=MovementType.IN,
                quantity=50,
                note="Initial demo stock entry",
            ),
            Notification(
                userId=installer.id,
                type=NotificationType.ORDER_ASSIGNED,
                title="New order assigned",
                message=f'You were assigned the order "{order.title}".',
                read=False,
            ),
            Notification(
                userId=supervisor.id,
                type=NotificationType.GENERAL,
                title="Seed completado",
                message="Datos demo cargados correctamente.",
                read=False,
            ),
        ]
    )
    db.commit()


def main_cli() -> None:
    assert_migrations_applied()
    with SessionLocal() as db:
        seed(db)
    print("Seed completed.")
    print(f"Demo login (all users): email *@isp.local password: {SEED_PASSWORD}")


if __name__ == "__main__":
    main_cli()
