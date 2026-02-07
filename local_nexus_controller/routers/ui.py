from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from local_nexus_controller.db import get_session
from local_nexus_controller.models import Database, KeyRef, Service
from local_nexus_controller.services.logs import tail_text_file
from local_nexus_controller.services.ports import is_port_in_use, next_available_port, port_map
from local_nexus_controller.services.process_manager import refresh_status


router = APIRouter(include_in_schema=False)

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    services = list(session.exec(select(Service)))
    dbs = list(session.exec(select(Database)))
    keys = list(session.exec(select(KeyRef)))

    running = 0
    stopped = 0
    error = 0
    alerts: list[str] = []
    for svc in services:
        refresh_status(session, svc)
        if svc.status == "running":
            running += 1
        elif svc.status == "error":
            error += 1
        else:
            stopped += 1

        if svc.port is not None and is_port_in_use("127.0.0.1", int(svc.port)) and svc.status != "running":
            alerts.append(f"Port conflict: {svc.name} reserved {svc.port} but is not running.")
        if not svc.start_command:
            alerts.append(f"Missing start_command: {svc.name}")

    session.commit()

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "totals": {
                "services": len(services),
                "running": running,
                "stopped": stopped,
                "error": error,
                "databases": len(dbs),
                "keys": len(keys),
                "ports_reserved": len([s for s in services if s.port is not None]),
            },
            "alerts": alerts[:10],
        },
    )


@router.get("/services", response_class=HTMLResponse)
def services_page(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    services = list(session.exec(select(Service).order_by(Service.name)))
    for svc in services:
        refresh_status(session, svc)
    session.commit()
    return templates.TemplateResponse(request, "services.html", {"services": services})


@router.get("/services/{service_id}", response_class=HTMLResponse)
def service_detail(request: Request, service_id: str, session: Session = Depends(get_session)) -> HTMLResponse:
    svc = session.get(Service, service_id)
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
    refresh_status(session, svc)
    session.commit()

    db = session.get(Database, svc.database_id) if svc.database_id else None
    keys = list(session.exec(select(KeyRef).where(KeyRef.service_id == svc.id).order_by(KeyRef.env_var)))

    log_tail = ""
    if svc.log_path:
        log_tail = tail_text_file(Path(svc.log_path), max_lines=200)

    port_in_use = is_port_in_use("127.0.0.1", int(svc.port)) if svc.port is not None else False

    return templates.TemplateResponse(
        request,
        "service_detail.html",
        {"service": svc, "database": db, "keys": keys, "log_tail": log_tail, "port_in_use": port_in_use},
    )


@router.get("/databases", response_class=HTMLResponse)
def databases_page(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    dbs = list(session.exec(select(Database).order_by(Database.database_name)))
    services = list(session.exec(select(Service).order_by(Service.name)))
    by_db: dict[str, list[Service]] = {}
    for svc in services:
        if svc.database_id:
            by_db.setdefault(svc.database_id, []).append(svc)
    return templates.TemplateResponse(request, "databases.html", {"databases": dbs, "linked": by_db})


@router.get("/ports", response_class=HTMLResponse)
def ports_page(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    ports = port_map(session, host="127.0.0.1")
    next_port = next_available_port(session, host="127.0.0.1")
    return templates.TemplateResponse(request, "ports.html", {"ports": ports, "next_port": next_port})


@router.get("/keys", response_class=HTMLResponse)
def keys_page(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    keys = list(session.exec(select(KeyRef).order_by(KeyRef.env_var)))
    services = {s.id: s for s in session.exec(select(Service))}
    return templates.TemplateResponse(request, "keys.html", {"keys": keys, "services": services})


@router.get("/import", response_class=HTMLResponse)
def import_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "import.html", {})
