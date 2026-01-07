# api-gateway/src/main.py
"""API Gateway main entry point with FastAPI and Telegram bot."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.db import init_postgres, close_postgres
from src.bot import create_bot, run_bot
from src.api import invoice, scriptclient, audit_sales, ads_alert, ocr

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting API Gateway...")
    bot_task = None

    try:
        # Initialize PostgreSQL (non-blocking, logs warning if not configured)
        init_postgres()
        logger.info("PostgreSQL initialization complete")
    except Exception as e:
        logger.error(f"PostgreSQL initialization error: {e}")

    try:
        # Start Telegram bot in background
        bot_task = asyncio.create_task(run_bot())
        logger.info("Telegram bot task started")
    except Exception as e:
        logger.error(f"Telegram bot startup error: {e}")

    logger.info("API Gateway startup complete - ready to serve requests")

    yield

    # Cleanup
    logger.info("Shutting down API Gateway...")
    if bot_task:
        bot_task.cancel()
        try:
            await bot_task
        except asyncio.CancelledError:
            pass

    close_postgres()
    logger.info("API Gateway shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="API Gateway",
    description="Unified API Gateway for Facebook-automation platform with Telegram bot",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(invoice.router, prefix="/api/invoice", tags=["invoice"])
app.include_router(scriptclient.router, prefix="/api/scriptclient", tags=["scriptclient"])
app.include_router(audit_sales.router, prefix="/api/audit-sales", tags=["audit-sales"])
app.include_router(ads_alert.router, prefix="/api/ads-alert", tags=["ads-alert"])
app.include_router(ocr.router, prefix="/api/ocr", tags=["ocr"])


@app.get("/", tags=["system"])
async def root():
    """API Gateway root endpoint."""
    return {
        "service": "api-gateway",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "invoice": "/api/invoice",
            "scriptclient": "/api/scriptclient",
            "audit_sales": "/api/audit-sales",
            "ads_alert": "/api/ads-alert",
            "ocr": "/api/ocr",
        }
    }


@app.get("/health", tags=["system"])
async def health():
    """Health check endpoint - responds quickly for Railway health checks."""
    return {
        "status": "ok",
        "service": "api-gateway",
    }


@app.get("/health/detailed", tags=["system"])
async def health_detailed():
    """Detailed health check with database status."""
    from src.db.postgres import get_db_session
    from sqlalchemy import text

    postgres_ok = False
    schemas_ok = {}

    try:
        with get_db_session() as db:
            # Check if schemas exist
            for schema in ["invoice", "scriptclient", "audit_sales", "ads_alert"]:
                result = db.execute(
                    text(f"SELECT schema_name FROM information_schema.schemata WHERE schema_name = :schema"),
                    {"schema": schema}
                ).fetchone()
                schemas_ok[schema] = result is not None
            postgres_ok = True
    except Exception as e:
        logger.error(f"Health check failed: {e}")

    return {
        "status": "ok" if postgres_ok else "degraded",
        "service": "api-gateway",
        "databases": {
            "postgresql": postgres_ok,
            "schemas": schemas_ok,
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
