"""
Railpack/Railway-friendly entrypoint.

Railpack will auto-start FastAPI apps if it can find an `app` object in
`app.py` or `main.py` at the repository root. This file provides that.
"""

from local_nexus_controller.main import app  # noqa: F401

