from __future__ import annotations

import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import psutil
from sqlmodel import Session

from local_nexus_controller.models import Service
from local_nexus_controller.settings import settings
from local_nexus_controller.services.ports import is_controller_port, is_port_in_use, next_available_port


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _service_log_path(service: Service) -> Path:
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in service.name)[:60]
    return settings.log_dir / f"{safe_name}-{service.id}.log"


def refresh_status(session: Session, service: Service) -> Service:
    """
    Update status based on tracked PID existence.
    """

    if service.process_pid is None:
        if service.status == "running":
            service.status = "stopped"
        return service

    if psutil.pid_exists(service.process_pid):
        try:
            p = psutil.Process(service.process_pid)
            if p.is_running() and p.status() != psutil.STATUS_ZOMBIE:
                service.status = "running"
                return service
        except psutil.Error:
            pass

    # PID no longer valid
    service.process_pid = None
    if service.status == "running":
        service.status = "stopped"
    return service


def start_service(session: Session, service: Service) -> Service:
    if not service.start_command:
        service.status = "error"
        service.last_error = "start_command is empty"
        return service

    service = refresh_status(session, service)
    if service.status == "running":
        return service

    # Self-heal: reassign port if it conflicts with the controller or is already in use.
    if service.port is not None:
        needs_reassign = is_controller_port(int(service.port))
        if not needs_reassign and is_port_in_use("127.0.0.1", int(service.port)) and service.status != "running":
            needs_reassign = True
        if needs_reassign:
            old_port = int(service.port)
            new_port = next_available_port(session, host="127.0.0.1")
            service.port = new_port
            if service.local_url and f":{old_port}" in service.local_url:
                service.local_url = service.local_url.replace(f":{old_port}", f":{new_port}")
            if service.healthcheck_url and f":{old_port}" in service.healthcheck_url:
                service.healthcheck_url = service.healthcheck_url.replace(f":{old_port}", f":{new_port}")
            session.add(service)
            session.commit()
            session.refresh(service)

    log_path = _service_log_path(service)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_f = log_path.open("a", encoding="utf-8", errors="replace")

    cmd = service.start_command
    if "{PORT}" in cmd:
        if service.port is None:
            stdout_f.close()
            service.status = "error"
            service.last_error = "start_command requires {PORT} but service.port is not set"
            return service
        cmd = cmd.replace("{PORT}", str(service.port))
    if "{HOST}" in cmd:
        cmd = cmd.replace("{HOST}", "127.0.0.1")

    env = os.environ.copy()
    # Common convention: many local servers respect PORT/HOST
    if service.port is not None:
        env.setdefault("PORT", str(service.port))
    env.setdefault("HOST", "127.0.0.1")

    # User-configured safe overrides (supports placeholders)
    for k, v in (service.env_overrides or {}).items():
        vv = str(v)
        if "{PORT}" in vv and service.port is not None:
            vv = vv.replace("{PORT}", str(service.port))
        if "{HOST}" in vv:
            vv = vv.replace("{HOST}", "127.0.0.1")
        env[str(k)] = vv

    try:
        proc = subprocess.Popen(
            cmd,
            shell=True,
            cwd=service.working_directory or None,
            stdout=stdout_f,
            stderr=stdout_f,
            env=env,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
        )
    except Exception as e:  # noqa: BLE001 (explicitly record error)
        stdout_f.close()
        service.status = "error"
        service.last_error = f"Failed to start: {e!r}"
        return service

    service.process_pid = int(proc.pid)
    service.process_started_at = _now_utc()
    service.status = "running"
    service.last_error = None
    service.log_path = str(log_path)

    # Convenience: fill local_url if missing and port is known
    if service.port and not service.local_url:
        service.local_url = f"http://127.0.0.1:{service.port}"

    service.updated_at = _now_utc()
    session.add(service)
    session.commit()
    session.refresh(service)
    return service


def _terminate_pid_tree(pid: int, timeout_s: float = 5.0) -> None:
    try:
        parent = psutil.Process(pid)
    except psutil.NoSuchProcess:
        return

    children = parent.children(recursive=True)
    for p in children:
        try:
            p.terminate()
        except psutil.Error:
            pass
    try:
        parent.terminate()
    except psutil.Error:
        pass

    gone, alive = psutil.wait_procs([parent, *children], timeout=timeout_s)
    for p in alive:
        try:
            p.kill()
        except psutil.Error:
            pass


def stop_service(session: Session, service: Service) -> Service:
    service = refresh_status(session, service)
    if service.status != "running" and service.process_pid is None:
        service.status = "stopped"
        service.updated_at = _now_utc()
        session.add(service)
        session.commit()
        session.refresh(service)
        return service

    if service.stop_command:
        cmd = service.stop_command
        if "{PORT}" in cmd and service.port is not None:
            cmd = cmd.replace("{PORT}", str(service.port))
        if "{HOST}" in cmd:
            cmd = cmd.replace("{HOST}", "127.0.0.1")
        env = os.environ.copy()
        if service.port is not None:
            env.setdefault("PORT", str(service.port))
        env.setdefault("HOST", "127.0.0.1")
        for k, v in (service.env_overrides or {}).items():
            vv = str(v)
            if "{PORT}" in vv and service.port is not None:
                vv = vv.replace("{PORT}", str(service.port))
            if "{HOST}" in vv:
                vv = vv.replace("{HOST}", "127.0.0.1")
            env[str(k)] = vv
        try:
            subprocess.run(
                cmd,
                shell=True,
                cwd=service.working_directory or None,
                capture_output=True,
                text=True,
                timeout=30,
                env=env,
            )
        except Exception:
            # Fall back to PID kill below.
            pass

    if service.process_pid is not None:
        _terminate_pid_tree(service.process_pid)

    service.process_pid = None
    service.status = "stopped"
    service.updated_at = _now_utc()
    session.add(service)
    session.commit()
    session.refresh(service)
    return service


def restart_service(session: Session, service: Service) -> Service:
    if service.restart_command:
        cmd = service.restart_command
        if "{PORT}" in cmd and service.port is not None:
            cmd = cmd.replace("{PORT}", str(service.port))
        if "{HOST}" in cmd:
            cmd = cmd.replace("{HOST}", "127.0.0.1")
        env = os.environ.copy()
        if service.port is not None:
            env.setdefault("PORT", str(service.port))
        env.setdefault("HOST", "127.0.0.1")
        for k, v in (service.env_overrides or {}).items():
            vv = str(v)
            if "{PORT}" in vv and service.port is not None:
                vv = vv.replace("{PORT}", str(service.port))
            if "{HOST}" in vv:
                vv = vv.replace("{HOST}", "127.0.0.1")
            env[str(k)] = vv
        try:
            subprocess.run(
                cmd,
                shell=True,
                cwd=service.working_directory or None,
                capture_output=True,
                text=True,
                timeout=60,
                env=env,
            )
            service.updated_at = _now_utc()
            session.add(service)
            session.commit()
            session.refresh(service)
            return service
        except Exception:
            # Fallback below.
            pass

    stop_service(session, service)
    # service object may be stale; refresh from DB after stop
    session.refresh(service)
    return start_service(session, service)
