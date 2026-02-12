"""
Health check and diagnostics API endpoints.
"""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel
from sqlmodel import Session, select

from local_nexus_controller.db import engine
from local_nexus_controller.models import Service
from local_nexus_controller.settings import settings


router = APIRouter()


class HealthStatus(BaseModel):
    status: str
    database: bool
    settings: dict
    features: dict
    warnings: list[str]
    errors: list[str]


@router.get("/health", response_model=HealthStatus)
def health_check() -> HealthStatus:
    """
    Comprehensive health check for the application.
    """
    warnings = []
    errors = []

    # Check database connectivity
    database_ok = False
    try:
        with Session(engine) as session:
            session.exec(select(Service)).first()
        database_ok = True
    except Exception as e:
        errors.append(f"Database error: {str(e)}")

    # Check critical paths
    if not settings.db_path.parent.exists():
        warnings.append(f"Database directory missing: {settings.db_path.parent}")

    if not settings.log_dir.exists():
        warnings.append(f"Log directory missing: {settings.log_dir}")
        try:
            settings.log_dir.mkdir(parents=True, exist_ok=True)
            warnings.append(f"Created log directory: {settings.log_dir}")
        except Exception as e:
            errors.append(f"Cannot create log directory: {e}")

    # Check auto-discovery folder
    if settings.auto_discovery_enabled and settings.repositories_folder:
        if not settings.repositories_folder.exists():
            warnings.append(f"Repositories folder missing: {settings.repositories_folder}")

    # Check file watcher folder
    if settings.file_watcher_enabled and settings.file_watcher_folder:
        if not settings.file_watcher_folder.exists():
            warnings.append(f"File watcher folder missing: {settings.file_watcher_folder}")

    # Determine overall status
    if errors:
        status = "error"
    elif warnings:
        status = "warning"
    else:
        status = "healthy"

    return HealthStatus(
        status=status,
        database=database_ok,
        settings={
            "port": settings.port,
            "host": settings.host,
            "reload": settings.reload,
            "auto_discovery_enabled": settings.auto_discovery_enabled,
            "file_watcher_enabled": settings.file_watcher_enabled,
            "auto_start_all_on_boot": settings.auto_start_all_on_boot,
        },
        features={
            "auto_discovery": settings.auto_discovery_enabled,
            "file_watcher": settings.file_watcher_enabled,
            "auto_start": settings.auto_start_all_on_boot,
            "live_reload": settings.reload,
        },
        warnings=warnings,
        errors=errors,
    )


class DiagnosticsInfo(BaseModel):
    python_version: str
    platform: str
    database_path: str
    database_exists: bool
    database_size_mb: float | None
    total_services: int
    running_services: int
    folders: dict


@router.get("/diagnostics", response_model=DiagnosticsInfo)
def diagnostics() -> DiagnosticsInfo:
    """
    Detailed diagnostics information.
    """
    # Get database info
    db_exists = settings.db_path.exists()
    db_size = None
    if db_exists:
        try:
            db_size = settings.db_path.stat().st_size / (1024 * 1024)  # Convert to MB
        except Exception:
            pass

    # Get service counts
    total_services = 0
    running_services = 0
    try:
        with Session(engine) as session:
            services = list(session.exec(select(Service)))
            total_services = len(services)
            running_services = sum(1 for s in services if s.status == "running")
    except Exception:
        pass

    return DiagnosticsInfo(
        python_version=sys.version,
        platform=sys.platform,
        database_path=str(settings.db_path),
        database_exists=db_exists,
        database_size_mb=db_size,
        total_services=total_services,
        running_services=running_services,
        folders={
            "project_root": str(settings.project_root),
            "db_path": str(settings.db_path.parent),
            "log_dir": str(settings.log_dir),
            "repositories_folder": str(settings.repositories_folder) if settings.repositories_folder else None,
            "file_watcher_folder": str(settings.file_watcher_folder) if settings.file_watcher_folder else None,
        },
    )
