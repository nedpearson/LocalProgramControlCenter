from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from local_nexus_controller.db import get_session
from local_nexus_controller.models import KeyRef, Service, ServiceCreate, ServiceUpdate
from local_nexus_controller.security import require_token
from local_nexus_controller.services.logs import tail_text_file
from local_nexus_controller.services.process_manager import refresh_status, restart_service, start_service, stop_service


router = APIRouter()


@router.get("")
def list_services(
    session: Session = Depends(get_session),
    category: str | None = Query(default=None),
    status: str | None = Query(default=None),
) -> list[Service]:
    q = select(Service)
    if category:
        q = q.where(Service.category == category)
    if status:
        q = q.where(Service.status == status)

    services = list(session.exec(q.order_by(Service.name)))
    changed = False
    for svc in services:
        before = (svc.status, svc.process_pid)
        refresh_status(session, svc)
        after = (svc.status, svc.process_pid)
        if after != before:
            svc.updated_at = svc.updated_at  # keep; updated in refresh if needed
            session.add(svc)
            changed = True

    if changed:
        session.commit()

    return services


@router.post("", dependencies=[Depends(require_token)])
def create_service(service_in: ServiceCreate, session: Session = Depends(get_session)) -> Service:
    svc = Service(**service_in.model_dump())  # type: ignore[attr-defined]
    session.add(svc)
    session.commit()
    session.refresh(svc)
    return svc


@router.get("/{service_id}")
def get_service(service_id: str, session: Session = Depends(get_session)) -> Service:
    svc = session.get(Service, service_id)
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
    refresh_status(session, svc)
    session.add(svc)
    session.commit()
    session.refresh(svc)
    return svc


@router.patch("/{service_id}", dependencies=[Depends(require_token)])
def update_service(service_id: str, patch: ServiceUpdate, session: Session = Depends(get_session)) -> Service:
    svc = session.get(Service, service_id)
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")

    data = patch.model_dump(exclude_unset=True)  # type: ignore[attr-defined]
    for k, v in data.items():
        setattr(svc, k, v)
    session.add(svc)
    session.commit()
    session.refresh(svc)
    return svc


@router.delete("/{service_id}", dependencies=[Depends(require_token)])
def delete_service(service_id: str, session: Session = Depends(get_session)) -> dict:
    svc = session.get(Service, service_id)
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")

    # Delete keys first
    keys = list(session.exec(select(KeyRef).where(KeyRef.service_id == svc.id)))
    for k in keys:
        session.delete(k)
    session.delete(svc)
    session.commit()
    return {"ok": True}


@router.post("/{service_id}/start", dependencies=[Depends(require_token)])
def api_start_service(service_id: str, session: Session = Depends(get_session)) -> Service:
    svc = session.get(Service, service_id)
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
    return start_service(session, svc)


@router.post("/{service_id}/stop", dependencies=[Depends(require_token)])
def api_stop_service(service_id: str, session: Session = Depends(get_session)) -> Service:
    svc = session.get(Service, service_id)
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
    return stop_service(session, svc)


@router.post("/{service_id}/restart", dependencies=[Depends(require_token)])
def api_restart_service(service_id: str, session: Session = Depends(get_session)) -> Service:
    svc = session.get(Service, service_id)
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
    return restart_service(session, svc)


@router.get("/{service_id}/logs")
def api_get_logs(
    service_id: str,
    session: Session = Depends(get_session),
    lines: int = Query(default=200, ge=1, le=2000),
) -> dict:
    svc = session.get(Service, service_id)
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")

    if not svc.log_path:
        return {"service_id": svc.id, "log_path": None, "tail": ""}

    log_path = Path(svc.log_path)
    return {"service_id": svc.id, "log_path": str(log_path), "tail": tail_text_file(log_path, max_lines=lines)}
