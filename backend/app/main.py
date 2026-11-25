"""FastAPI application entrypoint."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.database import SessionLocal
from app.routers import api_router
from app.seed import seed_demo_data

logger = logging.getLogger("uvicorn.error")
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Run optional demo data seeding in development mode on startup."""
    if settings.SEED_DEMO_DATA and settings.ENVIRONMENT != "test":
        db = SessionLocal()
        try:
            seed_demo_data(db)
        except Exception as exc:
            # Skip seeding if database or tables have not been initialized yet
            db.rollback()
            logger.warning(
                "Startup demo seeding skipped (%s). Ensure 'python init_db.py' and 'alembic upgrade head' have been run.",
                exc,
            )
        finally:
            db.close()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-grade Company Employee Management System REST API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """Liveness probe endpoint."""
    return {"status": "healthy", "service": settings.APP_NAME, "version": settings.APP_VERSION}
