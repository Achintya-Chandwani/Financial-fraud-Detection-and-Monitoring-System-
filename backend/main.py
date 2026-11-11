"""
FraudShield AI — FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from backend.app.core.config import settings
from backend.app.core.logging import setup_logging
from backend.app.database.connection import create_tables, check_db_connection
from backend.app.services.model_service import fraud_model
from backend.app.api import predictions, dashboard


# ─── Lifespan (startup / shutdown) ────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    setup_logging()
    logger.info("=" * 60)
    logger.info("FraudShield AI — Starting Up")
    logger.info("=" * 60)

    # Database
    if check_db_connection():
        logger.info("Database connection: OK")
        create_tables()
    else:
        logger.warning(
            "Database connection failed. Check your .env DB settings. "
            "The API will start but database features will not work."
        )

    # Load ML model
    model_loaded = fraud_model.load()
    if model_loaded:
        logger.info("ML model loaded successfully. Version={}", fraud_model.model_version)
    else:
        logger.warning(
            "ML model not found. "
            "Run notebooks 04_Model_Training.ipynb and 05_Model_Evaluation.ipynb to train a model."
        )

    logger.info("API ready at http://{}:{}", settings.API_HOST, settings.API_PORT)
    logger.info("API docs: http://{}:{}/docs", settings.API_HOST, settings.API_PORT)
    logger.info("=" * 60)

    yield  # Application runs here

    logger.info("FraudShield AI — Shutting Down")


# ─── FastAPI Application ───────────────────────────────────────────────────────

app = FastAPI(
    title       = "FraudShield AI",
    description = (
        "End-to-End Intelligent Fraud Detection Platform. "
        "Provides real-time fraud risk scoring, explainability, "
        "and investigation case management."
    ),
    version     = "1.0.0",
    docs_url    = "/docs",
    redoc_url   = "/redoc",
    lifespan    = lifespan,
)


# ─── CORS ─────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins     = settings.cors_origins,
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)


# ─── Global Exception Handler ─────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception on {}: {}", request.url, exc)
    return JSONResponse(
        status_code=500,
        content={
            "error":   "Internal server error",
            "message": str(exc),
            "path":    str(request.url),
        },
    )


# ─── Routers ──────────────────────────────────────────────────────────────────

app.include_router(predictions.router)
app.include_router(dashboard.router)


# ─── Root ─────────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def root():
    return {
        "name":        "FraudShield AI",
        "version":     "1.0.0",
        "status":      "running",
        "docs":        "/docs",
        "model_ready": fraud_model.is_loaded,
    }
