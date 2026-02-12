from __future__ import annotations

from pathlib import Path
from typing import Generator

from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine

from local_nexus_controller.settings import settings


def _ensure_parent_dir(path: Path) -> None:
    """Ensure the parent directory exists for the database file."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        print(f"✓ Database directory ready: {path.parent}")
    except Exception as e:
        print(f"✗ Failed to create database directory {path.parent}: {e}")
        raise


try:
    _ensure_parent_dir(settings.db_path)
    db_url = f"sqlite:///{settings.db_path.as_posix()}"
    print(f"✓ Database URL: {db_url}")
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False},
    )
except Exception as e:
    print(f"✗ Failed to initialize database engine: {e}")
    print(f"  Database path: {settings.db_path}")
    print(f"  Parent exists: {settings.db_path.parent.exists()}")
    print(f"  Path is absolute: {settings.db_path.is_absolute()}")
    raise


def init_db() -> None:
    """Initialize database with error handling."""
    try:
        SQLModel.metadata.create_all(engine)
        print("✓ Database tables created/verified")
    except Exception as e:
        print(f"✗ Failed to create database tables: {e}")
        raise

    try:
        _sqlite_migrate()
        print("✓ Database migrations applied")
    except Exception as e:
        print(f"⚠ Database migration warning: {e}")
        print("  Continuing anyway - migrations are optional")


def _sqlite_migrate() -> None:
    """
    Lightweight, additive migrations for local SQLite.
    We only ADD columns; never drop/rename.
    """
    try:
        with engine.begin() as conn:
            # Service.env_overrides (added in v0.2)
            cols = [row[1] for row in conn.execute(text("PRAGMA table_info(service)")).fetchall()]
            if cols and "env_overrides" not in cols:
                conn.execute(text("ALTER TABLE service ADD COLUMN env_overrides TEXT"))
                print("  ✓ Added column: service.env_overrides")
    except Exception as e:
        print(f"  ⚠ Migration failed: {e}")
        raise


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
