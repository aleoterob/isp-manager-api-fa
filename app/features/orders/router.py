from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_current_user, require_csrf, require_roles
from app.core.responses import EnvelopeRoute
from app.features.orders.dependencies import get_order_service
from app.features.orders.schemas import (
    DeletedOrderId,
    OrderCreate,
    OrderRead,
    OrderUpdate,
)
from app.features.orders.service import OrderService
from app.features.users.models import Role

router = APIRouter(
    prefix="/orders",
    tags=["orders"],
    dependencies=[Depends(get_current_user)],
    route_class=EnvelopeRoute,
)


@router.post(
    "",
    status_code=201,
    dependencies=[
        Depends(require_csrf),
        Depends(require_roles(Role.ADMIN, Role.SUPERVISOR)),
    ],
    response_model=OrderRead,
)
def create_order(
    dto: OrderCreate, service: Annotated[OrderService, Depends(get_order_service)]
):
    return service.create(dto)


@router.get("", response_model=list[OrderRead])
def list_orders(
    service: Annotated[OrderService, Depends(get_order_service)],
    skip: int = Query(0),
    take: int = Query(50),
):
    return service.find_all(skip=skip, take=take)


@router.get("/{order_id}", response_model=OrderRead)
def get_order(
    order_id: UUID, service: Annotated[OrderService, Depends(get_order_service)]
):
    return service.find_one(str(order_id))


@router.patch(
    "/{order_id}",
    dependencies=[
        Depends(require_csrf),
        Depends(require_roles(Role.ADMIN, Role.SUPERVISOR)),
    ],
    response_model=OrderRead,
)
def update_order(
    order_id: UUID,
    dto: OrderUpdate,
    service: Annotated[OrderService, Depends(get_order_service)],
):
    return service.update(str(order_id), dto)


@router.delete(
    "/{order_id}",
    dependencies=[
        Depends(require_csrf),
        Depends(require_roles(Role.ADMIN, Role.SUPERVISOR)),
    ],
    response_model=DeletedOrderId,
)
def delete_order(
    order_id: UUID, service: Annotated[OrderService, Depends(get_order_service)]
):
    return service.remove(str(order_id))
