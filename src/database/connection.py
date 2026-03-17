"""
Database connection management.

Provides a centralized SQLAlchemy engine and session factory,
used by all modules that need database access (subscriber, CRUD, ML, API).

Usage
-----
>>> from src.database.connection import get_engine, get_session, init_db
>>> engine = get_engine()                   # uses .env settings
>>> with get_session() as session:          # auto-commit/rollback context
...     session.execute(...)
>>> init_db()                               # create all tables
"""

import logging
import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Module-level singletons (initialized on first call)
_engine = None
_SessionFactory = None


def _build_db_url() -> str:
    """Build MySQL connection URL from environment variables."""
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "3306")
    name = os.getenv("DB_NAME", "hk_traffic")
    user = os.getenv("DB_USER", "traffic_user")
    password = os.getenv("DB_PASSWORD", "Traffic2025!")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}?charset=utf8mb4"


def get_engine(db_url: str | None = None):
    """
    Get or create the SQLAlchemy engine (singleton).

    Parameters
    ----------
    db_url : str, optional
        Explicit connection URL. If None, builds from .env variables.
        Only used on first call; subsequent calls return the cached engine.
    """
    global _engine
    if _engine is None:
        url = db_url or _build_db_url()
        _engine = create_engine(
            url,
            pool_size=5,
            max_overflow=10,
            pool_recycle=3600,
            pool_pre_ping=True,  # auto-reconnect on stale connections
            echo=False,
        )
        # Verify connection
        with _engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database engine created: %s", _engine.url.database)
    return _engine


def get_session_factory(db_url: str | None = None) -> sessionmaker:
    """Get or create the session factory (singleton)."""
    global _SessionFactory
    if _SessionFactory is None:
        engine = get_engine(db_url)
        _SessionFactory = sessionmaker(bind=engine)
    return _SessionFactory


@contextmanager
def get_session(db_url: str | None = None):
    """
    Context manager that provides a transactional session.

    Auto-commits on success, rolls back on exception, always closes.

    Usage
    -----
    >>> with get_session() as session:
    ...     session.execute(text("SELECT * FROM traffic_readings LIMIT 5"))
    """
    factory = get_session_factory(db_url)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    """Create all tables defined in models.py (if not exist)."""
    from src.database.models import Base
    engine = get_engine()
    Base.metadata.create_all(engine)
    logger.info("Database tables verified/created")


def dispose():
    """Close all connections. Call on application shutdown."""
    global _engine, _SessionFactory
    if _engine:
        _engine.dispose()
        _engine = None
        _SessionFactory = None
        logger.info("Database engine disposed")
