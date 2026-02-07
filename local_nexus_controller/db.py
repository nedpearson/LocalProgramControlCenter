from __future__ import annotations

from pathlib import Path
from typing import Generator

from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine

from local_nexus_controller.settings import settings


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


_ensure_parent_dir(settings.db_path)
engine = create_engine(
    f"sqlite:///{settings.db_path.as_posix()}",
    connect_args={"check_same_thread": False},
)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    _sqlite_migrate()


def _sqlite_migrate() -> None:
    """
    Lightweight, additive migrations for local SQLite.
    We only ADD columns; never drop/rename.
    """

    with engine.begin() as conn:
        # Service.env_overrides (added in v0.2)
        cols = [row[1] for row in conn.execute(text("PRAGMA table_info(service)")).fetchall()]
        if cols and "env_overrides" not in cols:
            conn.execute(text("ALTER TABLE service ADD COLUMN env_overrides TEXT"))


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
