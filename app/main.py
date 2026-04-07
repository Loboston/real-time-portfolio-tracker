import asyncio

import structlog
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.config import settings
from app.core.exceptions import AppError, app_error_handler
from app.core.logging import setup_logging

# Configure logging before anything else in the application
setup_logging(log_level=settings.log_level, json_logs=settings.is_production)

logger = structlog.get_logger(__name__)


def create_app() -> FastAPI:
    from contextlib import asynccontextmanager

    from app.api.health import router as health_router
    from app.api.v1.router import router as v1_router
    from app.cache.client import close_pool, get_redis_client
    from app.dependencies import engine
    from app.market_data.ingestor import run_ingestor
    from app.market_data.mock_provider import MockMarketDataProvider
    from app.websocket.router import router as ws_router
    from app.websocket.subscriber import run_subscriber

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("starting up", environment=settings.environment)

        redis = get_redis_client()
        try:
            await redis.ping()
            logger.info("redis connected")
        except Exception:
            logger.error("redis unavailable on startup — continuing anyway")
        finally:
            await redis.aclose()

        provider = MockMarketDataProvider()
        ingestor_task = asyncio.create_task(run_ingestor(provider))
        subscriber_task = asyncio.create_task(run_subscriber())

        yield

        ingestor_task.cancel()
        subscriber_task.cancel()

        logger.info("shutting down")
        await close_pool()
        await engine.dispose()

    app = FastAPI(
        title="Portfolio Tracker API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None if settings.is_production else "/redoc",
        swagger_ui_init_oauth={},
    )

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
        schema["components"]["securitySchemes"] = {
            "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
        }
        for path in schema.get("paths", {}).values():
            for operation in path.values():
                operation["security"] = [{"BearerAuth": []}]
        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi  # type: ignore[method-assign]

    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]

    app.include_router(health_router)
    app.include_router(v1_router)
    app.include_router(ws_router)

    return app


app = create_app()
