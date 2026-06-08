from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from app.api.dependencies import CurrentUser, get_current_user, require_csrf
from app.core.responses import EnvelopeRoute
from app.features.auth.dependencies import get_auth_service
from app.features.auth.schemas import (
    CsrfResponse,
    LoginRequest,
    LogoutResponse,
    SignupRequest,
)
from app.features.auth.service import AuthService
from app.features.users.schemas import UserRead

router = APIRouter(prefix="/auth", tags=["auth"], route_class=EnvelopeRoute)


@router.post(
    "/signup",
    status_code=201,
    response_model=UserRead,
    dependencies=[Depends(require_csrf)],
)
def signup(
    dto: SignupRequest,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    return service.signup(dto, response)


@router.post("/login", response_model=UserRead, dependencies=[Depends(require_csrf)])
def login(
    dto: LoginRequest,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    return service.login(dto.email, dto.password, response)


@router.post("/refresh", response_model=UserRead, dependencies=[Depends(require_csrf)])
def refresh(
    request: Request,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    return service.refresh(request, response)


@router.get("/csrf", response_model=CsrfResponse)
def csrf(
    response: Response, service: Annotated[AuthService, Depends(get_auth_service)]
):
    return service.issue_csrf_cookie(response)


@router.post(
    "/logout",
    response_model=LogoutResponse,
    dependencies=[Depends(get_current_user), Depends(require_csrf)],
)
def logout(
    request: Request,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    service.logout(request, response)
    return {"ok": True}


@router.get("/me", response_model=UserRead)
def me(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    return service.me(current_user.user_id)
