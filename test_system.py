#!/usr/bin/env python3
"""System test to verify all components work correctly."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    from local_nexus_controller import db, main, models, security, settings
    print("  OK: Core modules")

    from local_nexus_controller.routers import (
        api_autodiscovery, api_databases, api_health, api_import,
        api_keys, api_ports, api_services, api_summary, ui,
    )
    print("  OK: All routers")

    from local_nexus_controller.services import (
        auto_discovery, file_watcher, logs, ports, process_manager, registry_import,
    )
    print("  OK: All services")
    return True


def test_database():
    """Test database initialization."""
    print("Testing database...")

    from local_nexus_controller.db import init_db, engine
    from sqlmodel import Session, select
    from local_nexus_controller.models import Service

    init_db()
    print("  OK: Database initialized")

    with Session(engine) as session:
        services = list(session.exec(select(Service)))
        print(f"  OK: Database query works ({len(services)} services)")

    return True


def test_fastapi_app():
    """Test FastAPI application setup."""
    print("Testing FastAPI app...")

    from local_nexus_controller.main import app

    routes = [route.path for route in app.routes]
    print(f"  OK: Application created ({len(routes)} routes)")
    return True


def main():
    """Run all tests."""
    print("=" * 50)
    print("LOCAL NEXUS CONTROLLER - SYSTEM TEST")
    print("=" * 50)

    tests = [test_imports, test_database, test_fastapi_app]
    passed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  FAILED: {e}")

    print("=" * 50)
    print(f"RESULTS: {passed}/{len(tests)} passed")
    print("=" * 50)

    return 0 if passed == len(tests) else 1


if __name__ == "__main__":
    sys.exit(main())
