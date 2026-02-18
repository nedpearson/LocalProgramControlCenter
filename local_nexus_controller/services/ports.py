from __future__ import annotations

import socket
from dataclasses import dataclass

from sqlmodel import Session, select

from local_nexus_controller.models import Service
from local_nexus_controller.settings import settings


def is_port_in_use(host: str, port: int, timeout_s: float = 0.25) -> bool:
    """
    Returns True if something is accepting TCP connections on host:port.
    This is a pragmatic local check and works well for the common case.
    """

    try:
        with socket.create_connection((host, port), timeout=timeout_s):
            return True
    except OSError:
        return False


def controller_port() -> int:
    """Return the port the Nexus Controller itself is running on."""
    return settings.port


def reserved_ports(session: Session) -> set[int]:
    ports: set[int] = set()
    # Always reserve the controller's own port so no service collides with it.
    ports.add(controller_port())
    for p in session.exec(select(Service.port).where(Service.port.is_not(None))):
        if p is not None:
            ports.add(int(p))
    return ports


def is_controller_port(port: int) -> bool:
    """Check if a port is the Nexus Controller's own port."""
    return port == controller_port()


def next_available_port(
    session: Session,
    host: str = "127.0.0.1",
    start: int | None = None,
    end: int | None = None,
) -> int:
    start = start if start is not None else settings.port_range_start
    end = end if end is not None else settings.port_range_end
    reserved = reserved_ports(session)

    for port in range(start, end + 1):
        if port in reserved:
            continue
        if is_port_in_use(host, port):
            continue
        return port

    raise RuntimeError(f"No free port found in range {start}-{end}")


@dataclass(frozen=True)
class PortInfo:
    port: int
    reserved_by_service_id: str | None
    reserved_by_service_name: str | None
    in_use_on_host: bool
    conflict: bool


def port_map(
    session: Session,
    host: str = "127.0.0.1",
    start: int | None = None,
    end: int | None = None,
) -> list[PortInfo]:
    start = start if start is not None else settings.port_range_start
    end = end if end is not None else settings.port_range_end

    by_port: dict[int, Service] = {}
    for svc in session.exec(select(Service).where(Service.port.is_not(None))):
        if svc.port is not None:
            by_port[int(svc.port)] = svc

    out: list[PortInfo] = []
    for port in range(start, end + 1):
        svc = by_port.get(port)
        in_use = is_port_in_use(host, port)
        conflict = bool(svc) and in_use and (svc.status != "running")
        out.append(
            PortInfo(
                port=port,
                reserved_by_service_id=svc.id if svc else None,
                reserved_by_service_name=svc.name if svc else None,
                in_use_on_host=in_use,
                conflict=conflict,
            )
        )
    return out
