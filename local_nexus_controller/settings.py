from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _to_int(value: str | None, default: int) -> int:
    try:
        return int(value) if value is not None and value != "" else default
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    project_root: Path
    db_path: Path
    host: str
    port: int
    token: str | None
    port_range_start: int
    port_range_end: int
    log_dir: Path
    reload: bool


def load_settings() -> Settings:
    project_root = Path(__file__).resolve().parents[1]
    env_path = project_root / ".env"
    load_dotenv(env_path, override=False)

    db_path_raw = os.getenv("LOCAL_NEXUS_DB_PATH", "data/local_nexus.db")
    db_path = (project_root / db_path_raw).resolve() if not Path(db_path_raw).is_absolute() else Path(db_path_raw)

    host = os.getenv("LOCAL_NEXUS_HOST", "127.0.0.1")
    port = _to_int(os.getenv("LOCAL_NEXUS_PORT"), 5010)
    token = os.getenv("LOCAL_NEXUS_TOKEN") or None

    port_range_start = _to_int(os.getenv("LOCAL_NEXUS_PORT_RANGE_START"), 3000)
    port_range_end = _to_int(os.getenv("LOCAL_NEXUS_PORT_RANGE_END"), 3999)

    log_dir_raw = os.getenv("LOCAL_NEXUS_LOG_DIR", "data/logs")
    log_dir = (project_root / log_dir_raw).resolve() if not Path(log_dir_raw).is_absolute() else Path(log_dir_raw)

    reload = (os.getenv("LOCAL_NEXUS_RELOAD", "") or "").lower() in {"1", "true", "yes", "on"}

    return Settings(
        project_root=project_root,
        db_path=db_path,
        host=host,
        port=port,
        token=token,
        port_range_start=port_range_start,
        port_range_end=port_range_end,
        log_dir=log_dir,
        reload=reload,
    )


settings = load_settings()
