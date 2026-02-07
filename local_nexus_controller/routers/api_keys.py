from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from local_nexus_controller.db import get_session
from local_nexus_controller.models import KeyRef, KeyRefCreate, Service
from local_nexus_controller.security import require_token


router = APIRouter()


@router.get("")
def list_keys(session: Session = Depends(get_session)) -> list[dict]:
    keys = list(session.exec(select(KeyRef).order_by(KeyRef.env_var, KeyRef.key_name)))
    services = {s.id: s for s in session.exec(select(Service))}
    out: list[dict] = []
    for k in keys:
        svc = services.get(k.service_id)
        out.append(
            {
                "id": k.id,
                "key_name": k.key_name,
                "env_var": k.env_var,
                "description": k.description,
                "service": {"id": svc.id, "name": svc.name} if svc else None,
                "created_at": k.created_at,
            }
        )
    return out


@router.post("/services/{service_id}", dependencies=[Depends(require_token)])
def create_key(service_id: str, key_in: KeyRefCreate, session: Session = Depends(get_session)) -> KeyRef:
    svc = session.get(Service, service_id)
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")

    key = KeyRef(service_id=svc.id, **key_in.model_dump())  # type: ignore[attr-defined]
    session.add(key)
    session.commit()
    session.refresh(key)
    return key


@router.delete("/{key_id}", dependencies=[Depends(require_token)])
def delete_key(key_id: str, session: Session = Depends(get_session)) -> dict:
    key = session.get(KeyRef, key_id)
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    session.delete(key)
    session.commit()
    return {"ok": True}
