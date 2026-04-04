import structlog
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.cache.client import get_redis_client
from app.dependencies import async_session_factory

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/health", tags=["health"])
async def health_check() -> JSONResponse:
    status: dict[str, str] = {"status": "ok", "db": "unknown", "redis": "unknown"}
    http_status = 200

    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        status["db"] = "ok"
    except Exception:
        logger.exception("health check: database unreachable")
        status["db"] = "error"
        status["status"] = "degraded"
        http_status = 503

    try:
        redis = get_redis_client()
        await redis.ping()
        await redis.aclose()
        status["redis"] = "ok"
    except Exception:
        logger.exception("health check: redis unreachable")
        status["redis"] = "error"
        status["status"] = "degraded"
        http_status = 503

    return JSONResponse(content=status, status_code=http_status)
