"""
API routes for auto-discovery of programs in repository folders.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from local_nexus_controller.db import get_session
from local_nexus_controller.models import ImportBundle, Service
from local_nexus_controller.services.auto_discovery import (
    extract_and_scan_zip,
    scan_repository_folder,
)
from local_nexus_controller.services.registry_import import import_bundle


router = APIRouter()


class ScanRequest(BaseModel):
    folder_path: str
    auto_import: bool = False


class ScanResponse(BaseModel):
    discovered: int
    imported: int
    bundles: list[ImportBundle]


@router.post("/scan", response_model=ScanResponse)
def scan_folder(request: ScanRequest, session: Session = Depends(get_session)) -> ScanResponse:
    """
    Scan a folder for programs and optionally auto-import them.
    """
    folder_path = Path(request.folder_path)

    if not folder_path.exists():
        raise HTTPException(status_code=404, detail=f"Folder not found: {request.folder_path}")

    if not folder_path.is_dir():
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {request.folder_path}")

    # Get existing ports
    existing_services = list(session.exec(select(Service)))
    existing_ports = {s.port for s in existing_services if s.port is not None}

    # Scan for programs
    bundles = scan_repository_folder(str(folder_path), existing_ports)

    imported = 0
    if request.auto_import:
        for bundle in bundles:
            try:
                import_bundle(session, bundle)
                imported += 1
            except Exception as e:
                print(f"Failed to import {bundle.service.name}: {e}")

        session.commit()

    return ScanResponse(
        discovered=len(bundles),
        imported=imported,
        bundles=bundles,
    )


class ExtractZipRequest(BaseModel):
    zip_path: str
    extract_to: str
    auto_import: bool = True


class ExtractZipResponse(BaseModel):
    success: bool
    message: str
    bundle: ImportBundle | None = None


@router.post("/extract-zip", response_model=ExtractZipResponse)
def extract_zip(request: ExtractZipRequest, session: Session = Depends(get_session)) -> ExtractZipResponse:
    """
    Extract a ZIP file and auto-discover the program inside.
    """
    zip_path = Path(request.zip_path)
    extract_to = Path(request.extract_to)

    if not zip_path.exists():
        raise HTTPException(status_code=404, detail=f"ZIP file not found: {request.zip_path}")

    if not extract_to.exists():
        extract_to.mkdir(parents=True, exist_ok=True)

    bundle = extract_and_scan_zip(zip_path, extract_to)

    if not bundle:
        return ExtractZipResponse(
            success=False,
            message="No valid program found in ZIP file",
            bundle=None,
        )

    if request.auto_import:
        try:
            import_bundle(session, bundle)
            session.commit()
            return ExtractZipResponse(
                success=True,
                message=f"Successfully imported {bundle.service.name}",
                bundle=bundle,
            )
        except Exception as e:
            return ExtractZipResponse(
                success=False,
                message=f"Failed to import: {str(e)}",
                bundle=bundle,
            )

    return ExtractZipResponse(
        success=True,
        message="Program discovered but not imported (auto_import=false)",
        bundle=bundle,
    )
