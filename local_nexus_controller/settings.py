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
    open_browser: bool
    repositories_folder: Path | None
    auto_discovery_enabled: bool
    file_watcher_enabled: bool
    file_watcher_folder: Path | None
    auto_start_all_on_boot: bool


def load_settings() -> Settings:
    project_root = Path(__file__).resolve().parents[1]
    env_path = project_root / ".env"
    load_dotenv(env_path, override=False)

    db_path_raw = os.getenv("LOCAL_NEXUS_DB_PATH", "data/local_nexus.db")
    db_path = (project_root / db_path_raw).resolve() if not Path(db_path_raw).is_absolute() else Path(db_path_raw)

    # Deployment-friendly defaults:
    # - Platforms like Railway provide PORT; services must bind 0.0.0.0:$PORT.
    platform_port = os.getenv("PORT")
    host_default = "0.0.0.0" if platform_port else "127.0.0.1"
    host = os.getenv("LOCAL_NEXUS_HOST", host_default)

    port_raw = os.getenv("LOCAL_NEXUS_PORT") or platform_port
    port = _to_int(port_raw, 5010)
    token = os.getenv("LOCAL_NEXUS_TOKEN") or None

    port_range_start = _to_int(os.getenv("LOCAL_NEXUS_PORT_RANGE_START"), 3000)
    port_range_end = _to_int(os.getenv("LOCAL_NEXUS_PORT_RANGE_END"), 3999)

    log_dir_raw = os.getenv("LOCAL_NEXUS_LOG_DIR", "data/logs")
    log_dir = (project_root / log_dir_raw).resolve() if not Path(log_dir_raw).is_absolute() else Path(log_dir_raw)

    reload = (os.getenv("LOCAL_NEXUS_RELOAD", "") or "").lower() in {"1", "true", "yes", "on"}

    # Local convenience: auto-open dashboard in browser when launched via `python -m local_nexus_controller`.
    # Defaults to enabled for local runs and disabled for hosted platforms that provide PORT.
    open_browser_default = not bool(platform_port)
    open_browser = (os.getenv("LOCAL_NEXUS_OPEN_BROWSER", "") or "").lower() in {"1", "true", "yes", "on"}
    if os.getenv("LOCAL_NEXUS_OPEN_BROWSER") is None:
        open_browser = open_browser_default

    # Auto-discovery and file watcher settings
    repositories_folder_raw = os.getenv("LOCAL_NEXUS_REPOSITORIES_FOLDER")
    repositories_folder = Path(repositories_folder_raw) if repositories_folder_raw else None

    auto_discovery_enabled = (os.getenv("LOCAL_NEXUS_AUTO_DISCOVERY_ENABLED", "") or "").lower() in {"1", "true", "yes", "on"}

    file_watcher_enabled = (os.getenv("LOCAL_NEXUS_FILE_WATCHER_ENABLED", "") or "").lower() in {"1", "true", "yes", "on"}

    file_watcher_folder_raw = os.getenv("LOCAL_NEXUS_FILE_WATCHER_FOLDER")
    file_watcher_folder = Path(file_watcher_folder_raw) if file_watcher_folder_raw else None

    auto_start_all_on_boot = (os.getenv("LOCAL_NEXUS_AUTO_START_ALL_ON_BOOT", "") or "").lower() in {"1", "true", "yes", "on"}

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
        open_browser=open_browser,
        repositories_folder=repositories_folder,
        auto_discovery_enabled=auto_discovery_enabled,
        file_watcher_enabled=file_watcher_enabled,
        file_watcher_folder=file_watcher_folder,
        auto_start_all_on_boot=auto_start_all_on_boot,
    )


settings = load_settings()
