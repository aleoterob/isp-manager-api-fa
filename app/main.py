from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.db.models  # noqa: F401
from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.rate_limit import RateLimitMiddleware
from app.core.responses import EnvelopeRoute


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()
    app_settings.validate_runtime()
    configure_logging(app_settings)

    app = FastAPI(
        title=app_settings.app_name,
        docs_url="/docs" if app_settings.swagger_enabled else None,
        redoc_url="/redoc" if app_settings.swagger_enabled else None,
    )
    app.state.settings = app_settings
    app.router.route_class = EnvelopeRoute

    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.frontend_origins_list,
        allow_origin_regex=None
        if app_settings.frontend_origins_list
        else r"https?://.*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["Content-Type", "Authorization", "Accept", "X-CSRF-Token"],
    )

    register_exception_handlers(app)
    app.include_router(api_router)
    return app


app = create_app()
