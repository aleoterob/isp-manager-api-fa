from dataclasses import dataclass
from datetime import UTC, datetime
from http import HTTPStatus
from json import JSONDecodeError
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException


@dataclass(frozen=True)
class ErrorDefinition:
    code: str
    status: int
    message: str


class ErrorCode:
    VALIDATION_ERROR = ErrorDefinition("VALIDATION_ERROR", 400, "Validation error")
    INVALID_JSON = ErrorDefinition(
        "INVALID_JSON", 400, "The request body is not valid JSON"
    )
    INTERNAL_ERROR = ErrorDefinition(
        "INTERNAL_SERVER_ERROR", 500, "Internal server error"
    )
    DB_UNIQUE_VIOLATION = ErrorDefinition(
        "DB_UNIQUE_VIOLATION", 409, "A record with those values already exists"
    )
    USR_NOT_FOUND = ErrorDefinition("USR_NOT_FOUND", 404, "User not found")
    USR_EMAIL_TAKEN = ErrorDefinition(
        "USR_EMAIL_TAKEN", 409, "A user with that email already exists"
    )
    CUS_NOT_FOUND = ErrorDefinition("CUS_NOT_FOUND", 404, "Customer not found")
    CUS_COORDS_MISSING = ErrorDefinition(
        "CUS_COORDS_MISSING",
        400,
        "The customer does not have coordinates (latitude/longitude). "
        "Complete them before creating the order.",
    )
    USR_ROLE_INVALID_INSTALLER = ErrorDefinition(
        "USR_ROLE_INVALID_INSTALLER",
        400,
        "The selected user is not a valid active installer.",
    )
    ORD_NOT_FOUND = ErrorDefinition("ORD_NOT_FOUND", 404, "Order not found")
    AUTH_INVALID_CREDENTIALS = ErrorDefinition(
        "AUTH_INVALID_CREDENTIALS", 401, "Invalid credentials"
    )
    AUTH_UNAUTHENTICATED = ErrorDefinition(
        "AUTH_UNAUTHENTICATED", 401, "No autenticado"
    )
    AUTH_FORBIDDEN = ErrorDefinition(
        "AUTH_FORBIDDEN", 403, "You do not have permission to perform this action"
    )
    AUTH_REFRESH_INVALID = ErrorDefinition(
        "AUTH_REFRESH_INVALID", 401, "Invalid or expired refresh session"
    )
    AUTH_REFRESH_REUSE = ErrorDefinition(
        "AUTH_REFRESH_REUSE", 401, "Invalid session; sign in again"
    )
    CSRF_INVALID = ErrorDefinition("CSRF_INVALID", 403, "Invalid or missing CSRF token")


class AppException(Exception):
    def __init__(self, definition: ErrorDefinition) -> None:
        self.definition = definition
        super().__init__(definition.message)


def _is_unique_integrity_error(exc: IntegrityError) -> bool:
    orig = getattr(exc, "orig", None)
    sqlstate = getattr(orig, "sqlstate", None)
    if sqlstate == "23505":
        return True

    constraint_name = getattr(getattr(orig, "diag", None), "constraint_name", "")
    if constraint_name and (
        constraint_name.endswith("_key") or "unique" in constraint_name.lower()
    ):
        return True

    return "unique" in str(orig).lower()


def _timestamp() -> str:
    return (
        datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="milliseconds") + "Z"
    )


def _request_path(request: Request) -> str:
    return request.url.path + (f"?{request.url.query}" if request.url.query else "")


def error_body(
    request: Request,
    status_code: int,
    message: str,
    *,
    code: str | None = None,
    errors: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "success": False,
        "statusCode": status_code,
        "statusText": HTTPStatus(status_code).phrase,
        "timestamp": _timestamp(),
        "path": _request_path(request),
        "message": message,
    }
    if errors is not None:
        body["errors"] = errors
    if code is not None:
        body["code"] = code
    return body


def _validation_errors(
    exc: RequestValidationError,
) -> tuple[str, list[dict[str, Any]], str]:
    if any(err.get("type") == "json_invalid" for err in exc.errors()):
        return (
            ErrorCode.INVALID_JSON.message,
            [{"property": "body", "messages": [ErrorCode.INVALID_JSON.message]}],
            ErrorCode.INVALID_JSON.code,
        )

    grouped: dict[str, list[str]] = {}
    for err in exc.errors():
        loc = [
            str(part)
            for part in err.get("loc", [])
            if part not in {"body", "query", "path"}
        ]
        prop = ".".join(loc) or "body"
        grouped.setdefault(prop, []).append(str(err.get("msg", "Invalid value")))
    return (
        ErrorCode.VALIDATION_ERROR.message,
        [{"property": key, "messages": value} for key, value in grouped.items()],
        ErrorCode.VALIDATION_ERROR.code,
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request, exc: AppException
    ) -> JSONResponse:
        definition = exc.definition
        return JSONResponse(
            status_code=definition.status,
            content=error_body(
                request,
                definition.status,
                definition.message,
                code=definition.code,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        message, errors, code = _validation_errors(exc)
        return JSONResponse(
            status_code=400,
            content=error_body(request, 400, message, code=code, errors=errors),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(request, exc.status_code, str(exc.detail)),
        )

    @app.exception_handler(IntegrityError)
    async def integrity_handler(request: Request, exc: IntegrityError) -> JSONResponse:
        definition = (
            ErrorCode.DB_UNIQUE_VIOLATION
            if _is_unique_integrity_error(exc)
            else ErrorCode.INTERNAL_ERROR
        )
        return JSONResponse(
            status_code=definition.status,
            content=error_body(
                request, definition.status, definition.message, code=definition.code
            ),
        )

    @app.exception_handler(JSONDecodeError)
    async def json_handler(request: Request, exc: JSONDecodeError) -> JSONResponse:
        _ = exc
        definition = ErrorCode.INVALID_JSON
        return JSONResponse(
            status_code=definition.status,
            content=error_body(
                request,
                definition.status,
                definition.message,
                code=definition.code,
                errors=[{"property": "body", "messages": [definition.message]}],
            ),
        )
