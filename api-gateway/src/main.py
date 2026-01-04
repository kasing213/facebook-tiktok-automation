# api-gateway/src/main.py
"""API Gateway main entry point with FastAPI and Telegram bot."""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.db import init_postgres, close_postgres, mongo_manager
from src.bot import create_bot, run_bot
from src.api import invoice, scriptclient, audit_sales, ads_alert

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
        # Connect to MongoDB databases (with timeouts)
        await mongo_manager.connect()
        logger.info("MongoDB connections initialized")
    except Exception as e:
        logger.error(f"MongoDB connection error: {e}")

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

    await mongo_manager.close()
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
    try:
        mongo_status = await mongo_manager.health_check()
    except Exception:
        mongo_status = {"error": "check failed"}

    return {
        "status": "ok",
        "service": "api-gateway",
        "databases": {
            "postgresql": settings.DATABASE_URL != "",
            "mongodb": mongo_status,
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
