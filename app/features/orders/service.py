from sqlalchemy.orm import Session

from app.core.datetime import to_utc_naive
from app.core.errors import AppException, ErrorCode
from app.features.customers.repository import CustomerRepository
from app.features.orders.models import Order, OrderStatus
from app.features.orders.repository import OrderRepository
from app.features.orders.schemas import OrderCreate, OrderUpdate
from app.features.users.models import Role
from app.features.users.repository import UserRepository


class OrderService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = OrderRepository(db)
        self.customer_repository = CustomerRepository(db)
        self.user_repository = UserRepository(db)

    def find_all(self, skip: int = 0, take: int = 50) -> list[Order]:
        return self.repository.list(skip, take)

    def find_one(self, order_id: str) -> Order:
        order = self.repository.get(order_id)
        if not order:
            raise AppException(ErrorCode.ORD_NOT_FOUND)
        return order

    def _ensure_customer_with_coordinates(self, customer_id: str):
        customer = self.customer_repository.get(customer_id)
        if not customer:
            raise AppException(ErrorCode.CUS_NOT_FOUND)
        if customer.lat is None or customer.lng is None:
            raise AppException(ErrorCode.CUS_COORDS_MISSING)
        return customer

    def _ensure_installer(self, installer_id: str | None) -> None:
        if not installer_id:
            return
        installer = self.user_repository.get(installer_id)
        if not installer or not installer.active or installer.role != Role.INSTALLER:
            raise AppException(ErrorCode.USR_ROLE_INVALID_INSTALLER)

    def create(self, dto: OrderCreate) -> Order:
        customer = self._ensure_customer_with_coordinates(dto.customerId)
        self._ensure_installer(dto.installerId)
        order = Order(
            title=dto.title,
            description=dto.description,
            type=dto.type,
            status=OrderStatus.PENDING,
            customerId=customer.id,
            installerId=dto.installerId,
            address=customer.address,
            city=customer.city,
            province=customer.province,
            zipCode=customer.zipCode,
            lat=customer.lat,
            lng=customer.lng,
            scheduledAt=to_utc_naive(dto.scheduledAt),
        )
        self.db.add(order)
        self.db.commit()
        return self.find_one(order.id)

    def update(self, order_id: str, dto: OrderUpdate) -> Order:
        order = self.find_one(order_id)
        patch = dto.model_dump(exclude_unset=True)

        if "customerId" in patch and patch["customerId"] != order.customerId:
            customer = self._ensure_customer_with_coordinates(patch["customerId"])
            order.customerId = customer.id
            order.address = customer.address
            order.city = customer.city
            order.province = customer.province
            order.zipCode = customer.zipCode
            order.lat = customer.lat
            order.lng = customer.lng

        if "installerId" in patch:
            installer_id = patch["installerId"]
            if installer_id in {None, ""}:
                order.installerId = None
            else:
                self._ensure_installer(installer_id)
                order.installerId = installer_id

        for field in ["title", "description", "type", "status"]:
            if field in patch:
                setattr(order, field, patch[field])
        if "scheduledAt" in patch:
            order.scheduledAt = to_utc_naive(patch["scheduledAt"])

        self.db.commit()
        return self.find_one(order.id)

    def remove(self, order_id: str) -> dict[str, str]:
        order = self.find_one(order_id)
        self.repository.delete_related(order.id)
        self.db.delete(order)
        self.db.commit()
        return {"id": order_id}
