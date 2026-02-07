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
    services = list(session.exec(select(Service)))
    dbs = list(session.exec(select(Database)))
    keys = list(session.exec(select(KeyRef)))

    running = 0
    stopped = 0
    error = 0
    alerts: list[dict] = []

    for svc in services:
        refresh_status(session, svc)
        if svc.status == "running":
            running += 1
        elif svc.status == "error":
            error += 1
        else:
            stopped += 1

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

        if not svc.start_command:
            alerts.append(
                {
                    "type": "missing_start_command",
                    "message": f"{svc.name} has no start_command.",
                    "service_id": svc.id,
                }
            )

        if svc.config_paths is not None and len(svc.config_paths) == 0:
            # Not necessarily an error; keep low severity
            pass

    session.commit()

    ports_in_use = len([s for s in services if s.port is not None])

    return {
        "totals": {
            "services": len(services),
            "running": running,
            "stopped": stopped,
            "error": error,
            "databases": len(dbs),
            "keys": len(keys),
            "ports_reserved": ports_in_use,
        },
        "alerts": alerts,
    }
