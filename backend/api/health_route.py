"""GET /health: answers ok when the API is running."""

from fastapi import APIRouter

from backend.api.response_schemas import HealthResponse

health_router = APIRouter()


@health_router.get("/health")
async def check_health() -> HealthResponse:
    """Handles GET /health: answers that the API is running.

    Returns:
        Always {"status": "ok"}.

    Example:
        GET /health   # {"status": "ok"}
    """
    return HealthResponse(status="ok")
