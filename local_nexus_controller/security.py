from __future__ import annotations

from fastapi import Header, HTTPException

from local_nexus_controller.settings import settings


def require_token(x_local_nexus_token: str | None = Header(default=None)) -> None:
    """
    If LOCAL_NEXUS_TOKEN is set, require a matching X-Local-Nexus-Token header.
    Read-only endpoints should not depend on this.
    """

    if not settings.token:
        return

    if not x_local_nexus_token or x_local_nexus_token != settings.token:
        raise HTTPException(status_code=401, detail="Missing or invalid Local Nexus token")
