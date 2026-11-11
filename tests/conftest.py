"""
FraudShield AI — pytest configuration and fixtures

Uses an in-memory SQLite database so tests run without MySQL.
SQLAlchemy's Enum type is handled transparently by SQLite as VARCHAR.
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Point to SQLite in-memory — no MySQL needed for tests
SQLALCHEMY_TEST_URL = "sqlite://"

# Ensure the backend can be imported (project root on sys.path)
import sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Provide a dummy .env so Settings() doesn't fail on missing file
os.environ.setdefault("DB_HOST",     "localhost")
os.environ.setdefault("DB_PORT",     "3306")
os.environ.setdefault("DB_NAME",     "fraudshield_test")
os.environ.setdefault("DB_USER",     "root")
os.environ.setdefault("DB_PASSWORD", "")
os.environ.setdefault("APP_SECRET_KEY", "test_secret_key_32_characters_long")


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(
        SQLALCHEMY_TEST_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Enable foreign key enforcement in SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


@pytest.fixture(scope="session")
def setup_tables(test_engine):
    """Create all ORM tables in the SQLite test database."""
    from backend.app.database.connection import Base
    from backend.app.models import db_models  # noqa: F401 — registers models
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="session")
def client(test_engine, setup_tables):
    """
    FastAPI TestClient with the database dependency overridden
    to use SQLite instead of MySQL.
    """
    from backend.main import app
    from backend.app.database.connection import get_db

    TestSession = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def test_db(test_engine, setup_tables):
    """Direct DB session for unit tests that need raw DB access."""
    Session = sessionmaker(bind=test_engine)
    db = Session()
    yield db
    db.close()
