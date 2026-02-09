from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlmodel import Session, select

from local_nexus_controller.models import (
    Database,
    DatabaseCreate,
    ImportBundle,
    KeyRef,
    Service,
)
from local_nexus_controller.services.ports import is_port_in_use, next_available_port


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ImportResult:
    service_id: str
    database_id: str | None
    warnings: list[str]


def _upsert_database(session: Session, db_in: DatabaseCreate) -> Database:
    existing = session.exec(select(Database).where(Database.database_name == db_in.database_name)).first()
    if existing:
        for k, v in db_in.model_dump(exclude_unset=True).items():  # type: ignore[attr-defined]
            setattr(existing, k, v)
        existing.updated_at = _now_utc()
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing

    db = Database(**db_in.model_dump())  # type: ignore[attr-defined]
    db.created_at = _now_utc()
    db.updated_at = _now_utc()
    session.add(db)
    session.commit()
    session.refresh(db)
    return db


def _upsert_service(session: Session, svc_in: dict) -> Service:
    existing = session.exec(select(Service).where(Service.name == svc_in["name"])).first()
    if existing:
        for k, v in svc_in.items():
            setattr(existing, k, v)
        existing.updated_at = _now_utc()
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing

    svc = Service(**svc_in)
    svc.created_at = _now_utc()
    svc.updated_at = _now_utc()
    session.add(svc)
    session.commit()
    session.refresh(svc)
    return svc


def import_bundle(session: Session, bundle: ImportBundle, host_for_port_checks: str = "127.0.0.1") -> ImportResult:
    warnings: list[str] = []

    # Database
    database_id: str | None = None
    if bundle.database and bundle.auto_create_db:
        db = _upsert_database(session, bundle.database)
        database_id = db.id

    # Port assignment
    port: int | None = bundle.service.port
    if bundle.requested_port is not None:
        port = int(bundle.requested_port)
    if port is None and bundle.auto_assign_port:
        port = next_available_port(session, host=host_for_port_checks)

    # Check conflicts
    if port is not None:
        # Only warn if the port is reserved by a *different* service.
        conflicting = session.exec(
            select(Service).where(Service.port == int(port), Service.name != bundle.service.name)
        ).first()
        if conflicting:
            warnings.append(f"Port {port} is already reserved in the registry (by '{conflicting.name}').")
        if is_port_in_use(host_for_port_checks, port):
            warnings.append(f"Port {port} appears to be in use on {host_for_port_checks}.")

    # Upsert service
    svc_dict = bundle.service.model_dump()  # type: ignore[attr-defined]
    svc_dict["port"] = port
    if database_id is not None:
        svc_dict["database_id"] = database_id
    svc_dict.setdefault("status", "stopped")

    svc = _upsert_service(session, svc_dict)

    # Replace keys for service
    existing_keys = list(session.exec(select(KeyRef).where(KeyRef.service_id == svc.id)))
    for k in existing_keys:
        session.delete(k)
    session.commit()

    for key_in in bundle.keys or []:
        session.add(
            KeyRef(
                service_id=svc.id,
                key_name=key_in.key_name,
                env_var=key_in.env_var,
                description=key_in.description,
            )
        )
    session.commit()

    return ImportResult(service_id=svc.id, database_id=database_id, warnings=warnings)
