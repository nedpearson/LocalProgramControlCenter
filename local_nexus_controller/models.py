from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import Column
from sqlalchemy.types import JSON
from sqlmodel import Field, Relationship, SQLModel


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _uuid_str() -> str:
    return str(uuid.uuid4())


class Service(SQLModel, table=True):
    id: str = Field(default_factory=_uuid_str, primary_key=True, index=True)

    name: str = Field(index=True)
    description: str = Field(default="")
    category: str = Field(default="general", index=True)

    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    tech_stack: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    dependencies: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    config_paths: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    port: Optional[int] = Field(default=None, index=True)
    local_url: Optional[str] = Field(default=None)
    healthcheck_url: Optional[str] = Field(default=None)

    working_directory: Optional[str] = Field(default=None)
    start_command: str = Field(default="")
    stop_command: str = Field(default="")
    restart_command: str = Field(default="")

    # Environment overrides passed at runtime (safe values only; never secrets here).
    # Supports placeholders {PORT} and {HOST}.
    env_overrides: dict[str, str] = Field(default_factory=dict, sa_column=Column(JSON))

    # Runtime tracking
    status: str = Field(default="stopped", index=True)  # running|stopped|error|unknown
    process_pid: Optional[int] = Field(default=None, index=True)
    process_started_at: Optional[datetime] = Field(default=None)
    last_error: Optional[str] = Field(default=None)
    log_path: Optional[str] = Field(default=None)

    # Database linkage
    database_id: Optional[str] = Field(default=None, foreign_key="database.id", index=True)
    database_connection_string: Optional[str] = Field(default=None)
    database_schema_overview: Optional[str] = Field(default=None)

    created_at: datetime = Field(default_factory=_now_utc)
    updated_at: datetime = Field(default_factory=_now_utc)

    database: Optional["Database"] = Relationship(back_populates="services")
    keys: list["KeyRef"] = Relationship(back_populates="service")


class Database(SQLModel, table=True):
    id: str = Field(default_factory=_uuid_str, primary_key=True, index=True)

    database_name: str = Field(index=True, unique=True)
    type: str = Field(default="sqlite", index=True)  # sqlite|postgres|mysql|mongo|...

    host: Optional[str] = Field(default="localhost")
    port: Optional[int] = Field(default=None)

    username_env: Optional[str] = Field(default=None)
    password_env: Optional[str] = Field(default=None)

    connection_string: Optional[str] = Field(default=None)
    schema_overview: Optional[str] = Field(default=None)

    created_at: datetime = Field(default_factory=_now_utc)
    updated_at: datetime = Field(default_factory=_now_utc)

    services: list[Service] = Relationship(back_populates="database")


class KeyRef(SQLModel, table=True):
    id: str = Field(default_factory=_uuid_str, primary_key=True, index=True)

    service_id: str = Field(foreign_key="service.id", index=True)
    key_name: str = Field(index=True)
    env_var: str = Field(index=True)
    description: str = Field(default="")

    created_at: datetime = Field(default_factory=_now_utc)

    service: Service = Relationship(back_populates="keys")


# -----------------------
# API schemas (non-table)
# -----------------------

class ServiceCreate(SQLModel):
    name: str
    description: str = ""
    category: str = "general"
    tags: list[str] = Field(default_factory=list)
    tech_stack: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    config_paths: list[str] = Field(default_factory=list)
    port: Optional[int] = None
    local_url: Optional[str] = None
    healthcheck_url: Optional[str] = None
    working_directory: Optional[str] = None
    start_command: str = ""
    stop_command: str = ""
    restart_command: str = ""
    env_overrides: dict[str, str] = Field(default_factory=dict)
    database_id: Optional[str] = None
    database_connection_string: Optional[str] = None
    database_schema_overview: Optional[str] = None


class ServiceUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list[str]] = None
    tech_stack: Optional[list[str]] = None
    dependencies: Optional[list[str]] = None
    config_paths: Optional[list[str]] = None
    port: Optional[int] = None
    local_url: Optional[str] = None
    healthcheck_url: Optional[str] = None
    working_directory: Optional[str] = None
    start_command: Optional[str] = None
    stop_command: Optional[str] = None
    restart_command: Optional[str] = None
    env_overrides: Optional[dict[str, str]] = None
    database_id: Optional[str] = None
    database_connection_string: Optional[str] = None
    database_schema_overview: Optional[str] = None
    status: Optional[str] = None
    process_pid: Optional[int] = None
    last_error: Optional[str] = None
    log_path: Optional[str] = None


class DatabaseCreate(SQLModel):
    database_name: str
    type: str = "sqlite"
    host: Optional[str] = "localhost"
    port: Optional[int] = None
    username_env: Optional[str] = None
    password_env: Optional[str] = None
    connection_string: Optional[str] = None
    schema_overview: Optional[str] = None


class DatabaseUpdate(SQLModel):
    database_name: Optional[str] = None
    type: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username_env: Optional[str] = None
    password_env: Optional[str] = None
    connection_string: Optional[str] = None
    schema_overview: Optional[str] = None


class KeyRefCreate(SQLModel):
    key_name: str
    env_var: str
    description: str = ""


class ImportBundle(SQLModel):
    """
    This is the JSON shape used for auto-populating new programs.
    Paste this into the dashboard Import page or POST it to /api/import/bundle.
    """

    service: ServiceCreate
    database: Optional[DatabaseCreate] = None
    keys: list[KeyRefCreate] = Field(default_factory=list)
    requested_port: Optional[int] = None
    auto_assign_port: bool = True
    auto_create_db: bool = True
    meta: dict[str, Any] = Field(default_factory=dict)
