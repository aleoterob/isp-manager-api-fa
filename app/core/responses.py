import json
from collections.abc import Callable
from datetime import UTC, datetime
from http import HTTPStatus

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute


def _timestamp() -> str:
    return (
        datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="milliseconds") + "Z"
    )


def _path(request: Request) -> str:
    return request.url.path + (f"?{request.url.query}" if request.url.query else "")


class EnvelopeRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            response: Response = await original_route_handler(request)
            if response.status_code < 200 or response.status_code >= 300:
                return response
            if not hasattr(response, "body"):
                return response

            raw = getattr(response, "body", b"")
            data = json.loads(raw.decode("utf-8")) if raw else None
            content = {
                "success": True,
                "statusCode": response.status_code,
                "statusText": HTTPStatus(response.status_code).phrase,
                "timestamp": _timestamp(),
                "path": _path(request),
                "data": data,
            }
            wrapped = JSONResponse(status_code=response.status_code, content=content)
            for key, value in response.headers.items():
                if key.lower() not in {"content-length", "content-type"}:
                    wrapped.headers[key] = value
            wrapped.raw_headers.extend(
                header
                for header in response.raw_headers
                if header[0].lower() == b"set-cookie"
            )
            return wrapped

        return custom_route_handler
