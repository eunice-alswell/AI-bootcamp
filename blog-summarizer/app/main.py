from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.core.middleware import register_middleware


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    application = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        version=settings.app_version,
    )

    register_middleware(application, settings)
    application.include_router(api_router, prefix=settings.api_v1_prefix)

    return application


app = create_app()
