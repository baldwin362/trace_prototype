"""GET /health: answers ok when the API is running."""

from fastapi import APIRouter

from backend.api.response_schemas import HealthResponse

health_router = APIRouter()


@health_router.get("/health")
async def check_health() -> HealthResponse:
    return HealthResponse(status="ok")
