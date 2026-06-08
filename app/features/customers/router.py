from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_current_user
from app.core.responses import EnvelopeRoute
from app.features.customers.dependencies import get_customer_service
from app.features.customers.schemas import CustomerRead
from app.features.customers.service import CustomerService

router = APIRouter(
    prefix="/customers",
    tags=["customers"],
    dependencies=[Depends(get_current_user)],
    route_class=EnvelopeRoute,
)


@router.get("/search", response_model=list[CustomerRead])
def search_customers(
    service: Annotated[CustomerService, Depends(get_customer_service)],
    q: str = "",
    take: int = Query(10),
):
    return service.search(q, take)


@router.get("", response_model=list[CustomerRead])
def list_customers(
    service: Annotated[CustomerService, Depends(get_customer_service)],
    skip: int = Query(0),
    take: int = Query(50),
):
    return service.find_all(skip=skip, take=take)
