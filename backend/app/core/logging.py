"""
FraudShield AI — Logging Configuration
Configures loguru for structured, colored logging.
"""
import sys
from pathlib import Path
from loguru import logger
from backend.app.core.config import settings


def setup_logging() -> None:
    """Configure application-wide logging."""
    log_dir = Path(settings.LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # Remove default handler
    logger.remove()

    # Console handler — colored, human-readable
    logger.add(
        sys.stderr,
        level=settings.LOG_LEVEL,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # File handler — JSON-structured for production analysis
    logger.add(
        settings.LOG_FILE,
        level=settings.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} — {message}",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
    )

    logger.info("Logging initialized. Level={}", settings.LOG_LEVEL)
