from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from local_nexus_controller.db import get_session
from local_nexus_controller.models import Service
from local_nexus_controller.security import require_token
from local_nexus_controller.services.ports import is_port_in_use, next_available_port, port_map


router = APIRouter()


@router.get("/map")
def get_port_map(
    session: Session = Depends(get_session),
    host: str = Query(default="127.0.0.1"),
    start: int | None = Query(default=None),
    end: int | None = Query(default=None),
) -> list[dict]:
    return [p.__dict__ for p in port_map(session, host=host, start=start, end=end)]


@router.get("/next")
def get_next_port(
    session: Session = Depends(get_session),
    host: str = Query(default="127.0.0.1"),
) -> dict:
    return {"port": next_available_port(session, host=host)}


@router.post("/resolve-conflicts", dependencies=[Depends(require_token)])
def resolve_conflicts(
    session: Session = Depends(get_session),
    host: str = Query(default="127.0.0.1"),
) -> dict:
    """
    Reassign ports to eliminate conflicts:
    - Duplicate ports reserved by multiple services
    - Reserved ports that appear to be in use by *something else* while the service isn't running

    Also updates:
    - service.local_url / service.healthcheck_url when they embed the old port
    - dependent Vite apps' VITE_API_BASE_URL env override when dependencies move
    """

    services = list(session.exec(select(Service).order_by(Service.created_at)))

    by_port: dict[int, list[Service]] = {}
    for s in services:
        if s.port is not None:
            by_port.setdefault(int(s.port), []).append(s)

    changes: list[dict] = []

    def _pick_keeper(candidates: list[Service]) -> Service:
        # Keep a running service if possible, otherwise the first.
        for c in candidates:
            if c.status == "running" and c.process_pid is not None:
                return c
        return candidates[0]

    def _update_urls(svc: Service, old_port: int | None, new_port: int) -> None:
        if svc.local_url is None:
            svc.local_url = f"http://{host}:{new_port}"
        elif old_port is not None and f":{old_port}" in svc.local_url:
            svc.local_url = svc.local_url.replace(f":{old_port}", f":{new_port}")

        if svc.healthcheck_url is not None and old_port is not None and f":{old_port}" in svc.healthcheck_url:
            svc.healthcheck_url = svc.healthcheck_url.replace(f":{old_port}", f":{new_port}")

    # 1) Resolve duplicate reserved ports
    for port, owners in sorted(by_port.items(), key=lambda kv: kv[0]):
        if len(owners) <= 1:
            continue
        keeper = _pick_keeper(owners)
        for svc in owners:
            if svc.id == keeper.id:
                continue
            old_port = int(svc.port) if svc.port is not None else None
            new_port = next_available_port(session, host=host)
            svc.port = new_port
            _update_urls(svc, old_port=old_port, new_port=new_port)
            session.add(svc)
            changes.append(
                {
                    "service_id": svc.id,
                    "name": svc.name,
                    "reason": "duplicate_reserved_port",
                    "old_port": old_port,
                    "new_port": new_port,
                    "local_url": svc.local_url,
                }
            )

    session.commit()

    # Re-load after commits so subsequent checks see updated ports
    services = list(session.exec(select(Service).order_by(Service.created_at)))

    # 2) Resolve "port in use but service not running" conflicts
    for svc in services:
        if svc.port is None:
            continue
        port = int(svc.port)
        if svc.status == "running" and svc.process_pid is not None:
            continue
        if is_port_in_use(host, port):
            old_port = port
            new_port = next_available_port(session, host=host)
            svc.port = new_port
            _update_urls(svc, old_port=old_port, new_port=new_port)
            session.add(svc)
            changes.append(
                {
                    "service_id": svc.id,
                    "name": svc.name,
                    "reason": "port_in_use_on_host",
                    "old_port": old_port,
                    "new_port": new_port,
                    "local_url": svc.local_url,
                }
            )

    session.commit()

    # 3) Update dependent Vite apps: VITE_API_BASE_URL -> dependency local_url
    services = list(session.exec(select(Service).order_by(Service.name)))
    by_name = {s.name: s for s in services}

    dep_updates: list[dict] = []
    for svc in services:
        if not svc.dependencies:
            continue
        is_vite = any(x.lower() == "vite" for x in (svc.tech_stack or [])) or any("vite" in x.lower() for x in (svc.tags or []))
        if not is_vite:
            continue

        # Pick first dependency that has a local_url
        target_url = None
        for dep_name in svc.dependencies:
            dep = by_name.get(dep_name)
            if dep and dep.local_url:
                target_url = dep.local_url
                break
        if not target_url:
            continue

        env = dict(svc.env_overrides or {})
        if env.get("VITE_API_BASE_URL") != target_url:
            env["VITE_API_BASE_URL"] = target_url
            svc.env_overrides = env
            session.add(svc)
            dep_updates.append({"service_id": svc.id, "name": svc.name, "VITE_API_BASE_URL": target_url})

    if dep_updates:
        session.commit()

    return {"changes": changes, "dependent_env_updates": dep_updates}
