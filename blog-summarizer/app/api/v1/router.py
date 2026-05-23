from fastapi import APIRouter

from app.api.v1.routes import health, observability, summarization

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(observability.router, tags=["observability"])
api_router.include_router(summarization.router, tags=["summarization"])
