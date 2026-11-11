"""
FraudShield AI — Database Connection & Session Management
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from loguru import logger
from backend.app.core.config import settings


# SQLAlchemy engine — pool_pre_ping checks connection health
engine = create_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.APP_DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


def get_db():
    """FastAPI dependency — yields a database session and ensures cleanup."""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error("Database session error: {}", e)
        db.rollback()
        raise
    finally:
        db.close()


def check_db_connection() -> bool:
    """Check if database is reachable. Returns True on success."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error("Database connection failed: {}", e)
        return False


def create_tables() -> None:
    """Create all tables defined in ORM models (idempotent)."""
    from backend.app.models import db_models  # noqa: F401 — import triggers registration
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created.")
