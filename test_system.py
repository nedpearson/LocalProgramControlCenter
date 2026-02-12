#!/usr/bin/env python3
"""
Comprehensive system test to verify all components work correctly.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        from local_nexus_controller import db, main, models, security, settings
        print("  ✓ Core modules")
    except Exception as e:
        print(f"  ✗ Core modules failed: {e}")
        return False

    try:
        from local_nexus_controller.routers import (
            api_autodiscovery,
            api_databases,
            api_health,
            api_import,
            api_keys,
            api_ports,
            api_services,
            api_summary,
            ui,
        )
        print("  ✓ All routers")
    except Exception as e:
        print(f"  ✗ Routers failed: {e}")
        return False

    try:
        from local_nexus_controller.services import (
            auto_discovery,
            file_watcher,
            logs,
            ports,
            process_manager,
            registry_import,
        )
        print("  ✓ All services")
    except Exception as e:
        print(f"  ✗ Services failed: {e}")
        return False

    return True


def test_database():
    """Test database initialization."""
    print("\nTesting database...")

    try:
        from local_nexus_controller.db import init_db, engine
        from sqlmodel import Session, select
        from local_nexus_controller.models import Service

        init_db()
        print("  ✓ Database initialized")

        # Test database operations
        with Session(engine) as session:
            services = list(session.exec(select(Service)))
            print(f"  ✓ Database query works (found {len(services)} services)")

        return True
    except Exception as e:
        print(f"  ✗ Database failed: {e}")
        return False


def test_fastapi_app():
    """Test FastAPI application setup."""
    print("\nTesting FastAPI application...")

    try:
        from local_nexus_controller.main import app

        # Check routes are registered
        routes = [route.path for route in app.routes]
        print(f"  ✓ Application created ({len(routes)} routes)")

        # Check critical routes
        critical_routes = ["/", "/api/health", "/api/diagnostics", "/api/services", "/docs"]
        missing = [r for r in critical_routes if not any(r in route for route in routes)]

        if missing:
            print(f"  ⚠ Missing routes: {missing}")
        else:
            print("  ✓ All critical routes present")

        return True
    except Exception as e:
        print(f"  ✗ FastAPI app failed: {e}")
        return False


def test_settings():
    """Test settings loading."""
    print("\nTesting settings...")

    try:
        from local_nexus_controller.settings import settings

        print(f"  ✓ Settings loaded")
        print(f"    - Host: {settings.host}")
        print(f"    - Port: {settings.port}")
        print(f"    - Database: {settings.db_path}")
        print(f"    - Log dir: {settings.log_dir}")
        print(f"    - Auto-discovery: {settings.auto_discovery_enabled}")
        print(f"    - File watcher: {settings.file_watcher_enabled}")

        # Check paths exist or can be created
        if not settings.db_path.parent.exists():
            print(f"  ⚠ Database directory doesn't exist: {settings.db_path.parent}")

        if not settings.log_dir.exists():
            print(f"  ⚠ Log directory doesn't exist: {settings.log_dir}")

        return True
    except Exception as e:
        print(f"  ✗ Settings failed: {e}")
        return False


def test_static_files():
    """Test static files exist."""
    print("\nTesting static files...")

    try:
        from local_nexus_controller.settings import settings

        static_dir = settings.project_root / "local_nexus_controller" / "static"
        templates_dir = settings.project_root / "local_nexus_controller" / "templates"

        if not static_dir.exists():
            print(f"  ✗ Static directory missing: {static_dir}")
            return False

        if not templates_dir.exists():
            print(f"  ✗ Templates directory missing: {templates_dir}")
            return False

        # Check for key files
        app_js = static_dir / "app.js"
        styles_css = static_dir / "styles.css"

        if not app_js.exists():
            print(f"  ✗ Missing app.js")
            return False

        if not styles_css.exists():
            print(f"  ✗ Missing styles.css")
            return False

        # Check templates
        templates = ["base.html", "dashboard.html", "services.html", "import.html"]
        for tmpl in templates:
            if not (templates_dir / tmpl).exists():
                print(f"  ✗ Missing template: {tmpl}")
                return False

        print(f"  ✓ Static files present")
        print(f"  ✓ Templates present")

        return True
    except Exception as e:
        print(f"  ✗ Static files check failed: {e}")
        return False


def test_health_endpoints():
    """Test health check functionality."""
    print("\nTesting health endpoints...")

    try:
        from local_nexus_controller.routers.api_health import health_check, diagnostics

        # Test health check
        health = health_check()
        print(f"  ✓ Health check: {health.status}")
        print(f"    - Database: {'✓' if health.database else '✗'}")
        print(f"    - Warnings: {len(health.warnings)}")
        print(f"    - Errors: {len(health.errors)}")

        if health.errors:
            for error in health.errors:
                print(f"      ✗ {error}")

        if health.warnings:
            for warning in health.warnings:
                print(f"      ⚠ {warning}")

        # Test diagnostics
        diag = diagnostics()
        print(f"  ✓ Diagnostics")
        print(f"    - Python: {diag.python_version.split()[0]}")
        print(f"    - Platform: {diag.platform}")
        print(f"    - Services: {diag.total_services}")
        print(f"    - Running: {diag.running_services}")

        return True
    except Exception as e:
        print(f"  ✗ Health endpoints failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="* 60)
    print("LOCAL NEXUS CONTROLLER - SYSTEM TEST")
    print("="* 60)

    tests = [
        test_imports,
        test_settings,
        test_database,
        test_fastapi_app,
        test_static_files,
        test_health_endpoints,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n✗ Test crashed: {test.__name__}")
            print(f"  Error: {e}")
            failed += 1

    print("\n" + "="* 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="* 60)

    if failed == 0:
        print("✓ ALL TESTS PASSED - System is operational")
        return 0
    else:
        print("✗ SOME TESTS FAILED - Check errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
