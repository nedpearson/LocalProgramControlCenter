from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from sqlmodel import Session, select

from local_nexus_controller.db import engine, init_db
from local_nexus_controller.models import Service
from local_nexus_controller.routers.api_autodiscovery import router as api_autodiscovery_router
from local_nexus_controller.routers.api_databases import router as api_databases_router
from local_nexus_controller.routers.api_health import router as api_health_router
from local_nexus_controller.routers.api_import import router as api_import_router
from local_nexus_controller.routers.api_keys import router as api_keys_router
from local_nexus_controller.routers.api_ports import router as api_ports_router
from local_nexus_controller.routers.api_services import router as api_services_router
from local_nexus_controller.routers.api_summary import router as api_summary_router
from local_nexus_controller.routers.ui import router as ui_router
from local_nexus_controller.services.auto_discovery import scan_repository_folder
from local_nexus_controller.services.file_watcher import start_file_watcher
from local_nexus_controller.services.process_manager import start_service
from local_nexus_controller.services.registry_import import import_bundle
from local_nexus_controller.settings import settings


app = FastAPI(title="Local Nexus Controller", version="0.1.0")

static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

app.include_router(ui_router)
app.include_router(api_health_router, prefix="/api", tags=["health"])
app.include_router(api_services_router, prefix="/api/services", tags=["services"])
app.include_router(api_databases_router, prefix="/api/databases", tags=["databases"])
app.include_router(api_ports_router, prefix="/api/ports", tags=["ports"])
app.include_router(api_keys_router, prefix="/api/keys", tags=["keys"])
app.include_router(api_import_router, prefix="/api/import", tags=["import"])
app.include_router(api_summary_router, prefix="/api/summary", tags=["summary"])
app.include_router(api_autodiscovery_router, prefix="/api/autodiscovery", tags=["autodiscovery"])


@app.on_event("startup")
def _startup() -> None:
    """
    Initialize application on startup with comprehensive error handling.
    """
    # Initialize database with error recovery
    try:
        init_db()
        print("✓ Database initialized successfully")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        print("  Continuing anyway - some features may not work")

    # Auto-discovery: scan repositories folder on startup
    if settings.auto_discovery_enabled and settings.repositories_folder:
        try:
            if not settings.repositories_folder.exists():
                print(f"⚠ Auto-discovery folder not found: {settings.repositories_folder}")
                print("  Creating folder...")
                settings.repositories_folder.mkdir(parents=True, exist_ok=True)
                print(f"✓ Created: {settings.repositories_folder}")

            if settings.repositories_folder.exists():
                print(f"🔍 Auto-discovery: scanning {settings.repositories_folder}")
                try:
                    with Session(engine) as session:
                        existing_services = list(session.exec(select(Service)))
                        existing_ports = {s.port for s in existing_services if s.port is not None}
                        existing_names = {s.name for s in existing_services}

                        bundles = scan_repository_folder(str(settings.repositories_folder), existing_ports)

                        # Only import new services
                        imported = 0
                        for bundle in bundles:
                            if bundle.service.name not in existing_names:
                                try:
                                    import_bundle(session, bundle)
                                    imported += 1
                                    print(f"  ✓ Imported: {bundle.service.name}")
                                except Exception as e:
                                    print(f"  ✗ Failed to import {bundle.service.name}: {e}")

                        session.commit()
                        print(f"✓ Auto-discovery: imported {imported} new services")
                except Exception as e:
                    print(f"✗ Auto-discovery failed: {e}")
        except Exception as e:
            print(f"✗ Auto-discovery setup failed: {e}")

    # File watcher: start watching for ZIP files
    if settings.file_watcher_enabled and settings.file_watcher_folder and settings.repositories_folder:
        try:
            if not settings.file_watcher_folder.exists():
                print(f"⚠ File watcher folder not found: {settings.file_watcher_folder}")
                print("  File watcher will not start until folder exists")
            elif not settings.repositories_folder.exists():
                print(f"⚠ Repositories folder not found: {settings.repositories_folder}")
                print("  Creating folder for extracted programs...")
                settings.repositories_folder.mkdir(parents=True, exist_ok=True)
            else:
                start_file_watcher(
                    str(settings.file_watcher_folder),
                    str(settings.repositories_folder),
                )
                print(f"✓ File watcher started: {settings.file_watcher_folder}")
        except Exception as e:
            print(f"✗ File watcher failed to start: {e}")

    # Auto-start all services on boot
    if settings.auto_start_all_on_boot:
        try:
            print("🚀 Auto-start: starting all services")
            with Session(engine) as session:
                services = list(session.exec(select(Service)))
                started = 0
                failed = 0

                for svc in services:
                    if svc.start_command and svc.status != "running":
                        try:
                            start_service(session, svc)
                            started += 1
                            print(f"  ✓ Started: {svc.name}")
                        except Exception as e:
                            failed += 1
                            print(f"  ✗ Failed to start {svc.name}: {e}")

                session.commit()
                print(f"✓ Auto-start complete: {started} started, {failed} failed")
        except Exception as e:
            print(f"✗ Auto-start failed: {e}")
