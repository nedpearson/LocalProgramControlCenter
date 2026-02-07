from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from local_nexus_controller.db import init_db
from local_nexus_controller.routers.api_databases import router as api_databases_router
from local_nexus_controller.routers.api_import import router as api_import_router
from local_nexus_controller.routers.api_keys import router as api_keys_router
from local_nexus_controller.routers.api_ports import router as api_ports_router
from local_nexus_controller.routers.api_services import router as api_services_router
from local_nexus_controller.routers.api_summary import router as api_summary_router
from local_nexus_controller.routers.ui import router as ui_router


app = FastAPI(title="Local Nexus Controller", version="0.1.0")

static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

app.include_router(ui_router)
app.include_router(api_services_router, prefix="/api/services", tags=["services"])
app.include_router(api_databases_router, prefix="/api/databases", tags=["databases"])
app.include_router(api_ports_router, prefix="/api/ports", tags=["ports"])
app.include_router(api_keys_router, prefix="/api/keys", tags=["keys"])
app.include_router(api_import_router, prefix="/api/import", tags=["import"])
app.include_router(api_summary_router, prefix="/api/summary", tags=["summary"])


@app.on_event("startup")
def _startup() -> None:
    init_db()
