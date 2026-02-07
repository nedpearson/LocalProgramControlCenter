from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from local_nexus_controller.db import get_session
from local_nexus_controller.models import ImportBundle, KeyRef, Service
from local_nexus_controller.security import require_token
from local_nexus_controller.services.registry_import import import_bundle as import_bundle_impl


router = APIRouter()


@router.post("/bundle", dependencies=[Depends(require_token)])
def import_bundle(bundle: ImportBundle, session: Session = Depends(get_session)) -> dict:
    res = import_bundle_impl(session, bundle)
    return {"service_id": res.service_id, "database_id": res.database_id, "warnings": res.warnings}


@router.get("/bundle-template")
def bundle_template() -> dict:
    return {
        "service": {
            "name": "My New Local Service",
            "description": "What it does / why it exists",
            "category": "apps",
            "tags": ["local", "prototype"],
            "tech_stack": ["python", "fastapi"],
            "dependencies": [],
            "config_paths": [],
            "port": None,
            "local_url": None,
            "healthcheck_url": None,
            "working_directory": "C:/path/to/project",
            "start_command": "python -m uvicorn app.main:app --port 8001",
            "stop_command": "",
            "restart_command": "",
            "env_overrides": {
                "PORT": "{PORT}",
                "HOST": "{HOST}"
            },
            "database_id": None,
            "database_connection_string": None,
            "database_schema_overview": None,
        },
        "database": {
            "database_name": "my_service_db",
            "type": "sqlite",
            "host": "localhost",
            "port": None,
            "username_env": None,
            "password_env": None,
            "connection_string": "sqlite:///./data/my_service.db",
            "schema_overview": "tables: ...",
        },
        "keys": [
            {"key_name": "OpenAI API Key", "env_var": "OPENAI_API_KEY", "description": "Used for LLM calls"}
        ],
        "requested_port": 3100,
        "auto_assign_port": True,
        "auto_create_db": True,
        "meta": {
            "generated_by": "assistant",
            "notes": "Paste into dashboard Import"
        },
    }


@router.get("/env-example")
def env_example(session: Session = Depends(get_session)) -> dict:
    """
    Generates a combined .env.example style listing of *references* (never values).
    """

    services = list(session.exec(select(Service).order_by(Service.name)))
    keys = list(session.exec(select(KeyRef).order_by(KeyRef.env_var)))
    keys_by_service: dict[str, list[KeyRef]] = {}
    for k in keys:
        keys_by_service.setdefault(k.service_id, []).append(k)

    lines: list[str] = []
    lines.append("# Local Nexus Controller - referenced keys (example)")
    lines.append("# NOTE: This file contains references only. Do not put real secrets in source control.")
    lines.append("")

    for svc in services:
        svc_keys = keys_by_service.get(svc.id, [])
        if not svc_keys:
            continue
        lines.append(f"### {svc.name}")
        for k in svc_keys:
            comment = f" # {k.key_name}" + (f" ({k.description})" if k.description else "")
            lines.append(f"{k.env_var}={comment}")
        lines.append("")

    return {"env_example": "\n".join(lines).rstrip() + "\n"}
