from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_current_user, require_csrf, require_roles
from app.core.responses import EnvelopeRoute
from app.features.users.dependencies import get_user_service
from app.features.users.models import Role
from app.features.users.schemas import UserCreate, UserRead, UserUpdate
from app.features.users.service import UserService

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(get_current_user)],
    route_class=EnvelopeRoute,
)


@router.post(
    "",
    status_code=201,
    dependencies=[Depends(require_csrf), Depends(require_roles(Role.ADMIN))],
    response_model=UserRead,
)
def create_user(
    dto: UserCreate, service: Annotated[UserService, Depends(get_user_service)]
):
    return service.create(dto)


@router.get("", response_model=list[UserRead])
def list_users(
    service: Annotated[UserService, Depends(get_user_service)],
    skip: int = Query(0),
    take: int = Query(50),
    activeOnly: str | None = None,
    role: Role | None = None,
):
    return service.find_all(
        skip=skip, take=take, active_only=activeOnly == "true", role=role
    )


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: UUID, service: Annotated[UserService, Depends(get_user_service)]
):
    return service.find_one(str(user_id))


@router.patch(
    "/{user_id}",
    dependencies=[Depends(require_csrf), Depends(require_roles(Role.ADMIN))],
    response_model=UserRead,
)
def update_user(
    user_id: UUID,
    dto: UserUpdate,
    service: Annotated[UserService, Depends(get_user_service)],
):
    return service.update(str(user_id), dto)


@router.delete(
    "/{user_id}",
    dependencies=[Depends(require_csrf), Depends(require_roles(Role.ADMIN))],
    response_model=UserRead,
)
def delete_user(
    user_id: UUID, service: Annotated[UserService, Depends(get_user_service)]
):
    return service.remove(str(user_id))
