from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from local_nexus_controller.db import get_session
from local_nexus_controller.models import Database, DatabaseCreate, DatabaseUpdate, Service
from local_nexus_controller.security import require_token


router = APIRouter()


@router.get("")
def list_databases(session: Session = Depends(get_session)) -> list[Database]:
    return list(session.exec(select(Database).order_by(Database.database_name)))


@router.post("", dependencies=[Depends(require_token)])
def create_database(db_in: DatabaseCreate, session: Session = Depends(get_session)) -> Database:
    db = Database(**db_in.model_dump())  # type: ignore[attr-defined]
    session.add(db)
    session.commit()
    session.refresh(db)
    return db


@router.get("/{database_id}")
def get_database(database_id: str, session: Session = Depends(get_session)) -> dict:
    db = session.get(Database, database_id)
    if not db:
        raise HTTPException(status_code=404, detail="Database not found")

    linked = list(session.exec(select(Service).where(Service.database_id == db.id).order_by(Service.name)))
    safe = db.model_dump()  # type: ignore[attr-defined]
    safe["linked_services"] = [{"id": s.id, "name": s.name, "status": s.status, "port": s.port} for s in linked]
    return safe


@router.patch("/{database_id}", dependencies=[Depends(require_token)])
def update_database(database_id: str, patch: DatabaseUpdate, session: Session = Depends(get_session)) -> Database:
    db = session.get(Database, database_id)
    if not db:
        raise HTTPException(status_code=404, detail="Database not found")

    data = patch.model_dump(exclude_unset=True)  # type: ignore[attr-defined]
    for k, v in data.items():
        setattr(db, k, v)
    session.add(db)
    session.commit()
    session.refresh(db)
    return db


@router.delete("/{database_id}", dependencies=[Depends(require_token)])
def delete_database(database_id: str, session: Session = Depends(get_session)) -> dict:
    db = session.get(Database, database_id)
    if not db:
        raise HTTPException(status_code=404, detail="Database not found")

    # Unlink services
    linked = list(session.exec(select(Service).where(Service.database_id == db.id)))
    for svc in linked:
        svc.database_id = None
        session.add(svc)

    session.delete(db)
    session.commit()
    return {"ok": True}
