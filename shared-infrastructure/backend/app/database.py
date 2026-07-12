"""SQLAlchemy session/engine setup.

SQLite by default so the whole stack runs in any container tonight; production
is PostgreSQL via GEOAR_DATABASE_URL (e.g. postgresql+psycopg://...) — models
use portable column types only.
"""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Default SQLite file lives next to the backend package (absolute path), so the
# API, seed script and self-learning runner all hit the same DB regardless of cwd.
_DEFAULT_SQLITE = f"sqlite:///{Path(__file__).parents[1] / 'geoar.db'}"
DATABASE_URL = os.environ.get("GEOAR_DATABASE_URL", _DEFAULT_SQLITE)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
