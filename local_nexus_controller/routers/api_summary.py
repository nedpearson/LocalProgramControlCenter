from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from local_nexus_controller.db import get_session
from local_nexus_controller.models import Database, KeyRef, Service
from local_nexus_controller.services.ports import is_port_in_use
from local_nexus_controller.services.process_manager import refresh_status


router = APIRouter()


@router.get("")
def summary(session: Session = Depends(get_session)) -> dict:
    services = list(session.exec(select(Service).order_by(Service.name)))
    dbs = list(session.exec(select(Database)))
    keys = list(session.exec(select(KeyRef)))

    running_services = []
    stopped_services = []
    error_services = []
    alerts: list[dict] = []

    for svc in services:
        refresh_status(session, svc)
        svc_data = {
            "id": svc.id,
            "name": svc.name,
            "port": svc.port,
            "status": svc.status,
            "has_start_command": bool(svc.start_command),
        }

        if svc.status == "running":
            running_services.append(svc_data)
        elif svc.status == "error":
            error_services.append(svc_data)
        else:
            stopped_services.append(svc_data)

        if svc.port is not None:
            in_use = is_port_in_use("127.0.0.1", int(svc.port))
            if in_use and svc.status != "running":
                alerts.append(
                    {
                        "type": "port_conflict",
                        "message": f"Port {svc.port} is in use but {svc.name} is not running.",
                        "service_id": svc.id,
                    }
                )

        if not svc.start_command and (svc.category or "").lower() not in {"repo", "repos"}:
            alerts.append(
                {
                    "type": "missing_start_command",
                    "message": f"{svc.name} has no start_command.",
                    "service_id": svc.id,
                }
            )

    session.commit()

    ports_in_use = len([s for s in services if s.port is not None])

    return {
        "services": len(services),
        "running": len(running_services),
        "stopped": len(stopped_services),
        "error": len(error_services),
        "databases": len(dbs),
        "keys": len(keys),
        "ports_reserved": ports_in_use,
        "running_services": running_services,
        "stopped_services": stopped_services[:10],
        "error_services": error_services,
        "alerts": alerts,
    }
