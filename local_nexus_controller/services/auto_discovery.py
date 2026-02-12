"""
Auto-discovery service for scanning repository folders and auto-importing programs.
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Optional

from local_nexus_controller.models import ImportBundle, ServiceCreate, DatabaseCreate, KeyRefCreate


def detect_program_type(repo_path: Path) -> Optional[str]:
    """Detect the type of program in a repository with error handling."""
    try:
        if not repo_path.exists() or not repo_path.is_dir():
            return None

        if (repo_path / "package.json").exists():
            return "nodejs"
        if (repo_path / "requirements.txt").exists() or (repo_path / "pyproject.toml").exists():
            return "python"
        if (repo_path / "go.mod").exists():
            return "go"
        if (repo_path / "Cargo.toml").exists():
            return "rust"
        if (repo_path / "pom.xml").exists() or (repo_path / "build.gradle").exists():
            return "java"
        if (repo_path / ".csproj").exists():
            return "dotnet"
        return None
    except Exception:
        return None


def get_default_port(program_type: str, existing_ports: set[int]) -> int:
    """Get a default port based on program type, avoiding conflicts."""
    base_ports = {
        "nodejs": 3000,
        "python": 5000,
        "go": 8080,
        "rust": 8000,
        "java": 8080,
        "dotnet": 5000,
    }
    base = base_ports.get(program_type, 3000)
    port = base
    while port in existing_ports:
        port += 1
    return port


def extract_package_info(repo_path: Path, program_type: str) -> dict:
    """Extract program information from config files."""
    info = {
        "name": repo_path.name,
        "description": "",
        "dependencies": [],
        "scripts": {},
    }

    if program_type == "nodejs" and (repo_path / "package.json").exists():
        try:
            with open(repo_path / "package.json", encoding="utf-8") as f:
                pkg = json.load(f)
                info["name"] = pkg.get("name", repo_path.name)
                info["description"] = pkg.get("description", "")
                info["dependencies"] = list(pkg.get("dependencies", {}).keys())
                info["scripts"] = pkg.get("scripts", {})
        except Exception:
            pass

    return info


def generate_start_command(repo_path: Path, program_type: str, info: dict) -> str:
    """Generate appropriate start command based on program type."""
    scripts = info.get("scripts", {})

    if program_type == "nodejs":
        if "dev" in scripts:
            return f"cd {repo_path} && npm run dev"
        elif "start" in scripts:
            return f"cd {repo_path} && npm start"
        else:
            return f"cd {repo_path} && node index.js"

    elif program_type == "python":
        if (repo_path / "main.py").exists():
            return f"cd {repo_path} && python main.py"
        elif (repo_path / "app.py").exists():
            return f"cd {repo_path} && python app.py"
        elif (repo_path / "manage.py").exists():
            return f"cd {repo_path} && python manage.py runserver {'{PORT}'}"
        else:
            return f"cd {repo_path} && python -m uvicorn main:app --host 0.0.0.0 --port {'{PORT}'}"

    elif program_type == "go":
        return f"cd {repo_path} && go run ."

    elif program_type == "rust":
        return f"cd {repo_path} && cargo run"

    return ""


def scan_repository_folder(folder_path: str, existing_ports: set[int]) -> list[ImportBundle]:
    """
    Scan a folder for repositories and ZIP files, generate import bundles.

    Args:
        folder_path: Path to the folder containing repositories
        existing_ports: Set of already allocated ports

    Returns:
        List of ImportBundle objects for discovered programs
    """
    bundles = []

    try:
        folder = Path(folder_path)

        if not folder.exists():
            return bundles

        if not folder.is_dir():
            return bundles

        zip_files_to_process = []
        dirs_to_scan = []

        for item in folder.iterdir():
            try:
                if item.name.startswith("."):
                    continue

                if item.is_file() and item.suffix.lower() == ".zip":
                    zip_files_to_process.append(item)
                elif item.is_dir():
                    skip_folders = {"node_modules", ".git", "__pycache__", "venv", ".venv", "dist", "build"}
                    if item.name not in skip_folders:
                        dirs_to_scan.append(item)
            except Exception:
                continue

        for zip_path in zip_files_to_process:
            try:
                extracted_dir = folder / zip_path.stem
                if extracted_dir.exists():
                    continue

                if not zipfile.is_zipfile(zip_path):
                    continue

                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    total_size = sum(info.file_size for info in zip_ref.infolist())
                    if total_size > 1024 * 1024 * 1024:
                        continue
                    zip_ref.extractall(extracted_dir)

                dirs_to_scan.append(extracted_dir)
            except Exception:
                continue

        for repo_path in dirs_to_scan:
            try:
                program_type = detect_program_type(repo_path)
                if not program_type:
                    for subdir in repo_path.iterdir():
                        if subdir.is_dir() and not subdir.name.startswith("."):
                            program_type = detect_program_type(subdir)
                            if program_type:
                                repo_path = subdir
                                break

                if not program_type:
                    continue

                info = extract_package_info(repo_path, program_type)
                port = get_default_port(program_type, existing_ports)
                existing_ports.add(port)

                safe_name = info["name"].replace("@", "").replace("/", "-")[:100]

                service = ServiceCreate(
                    name=safe_name,
                    description=info["description"] or f"Auto-discovered {program_type} program",
                    category="auto-discovered",
                    tags=["auto-discovered", program_type],
                    tech_stack=[program_type],
                    dependencies=info["dependencies"][:10],
                    config_paths=[str(repo_path)],
                    port=port,
                    local_url=f"http://localhost:{port}",
                    healthcheck_url=f"http://localhost:{port}/health",
                    working_directory=str(repo_path),
                    start_command=generate_start_command(repo_path, program_type, info),
                    stop_command="",
                    restart_command="",
                    env_overrides={"PORT": str(port)},
                )

                bundle = ImportBundle(
                    service=service,
                    requested_port=port,
                    auto_assign_port=False,
                    auto_create_db=False,
                    meta={
                        "source": "auto_discovery",
                        "program_type": program_type,
                        "discovered_at": str(repo_path),
                    },
                )

                bundles.append(bundle)
            except Exception:
                continue

    except Exception:
        pass

    return bundles


def extract_and_scan_zip(zip_path: Path, extract_to: Path) -> Optional[ImportBundle]:
    """
    Extract a ZIP file and scan it for a program to import with comprehensive error handling.

    Args:
        zip_path: Path to the ZIP file
        extract_to: Folder to extract to

    Returns:
        ImportBundle if a valid program is found, None otherwise
    """
    try:
        # Validate inputs
        if not zip_path.exists():
            print(f"✗ ZIP file not found: {zip_path}")
            return None

        if not zipfile.is_zipfile(zip_path):
            print(f"✗ File is not a valid ZIP: {zip_path}")
            return None

        # Ensure extraction folder exists
        extract_to.mkdir(parents=True, exist_ok=True)

        # Create extraction folder with unique name
        program_name = zip_path.stem
        target_dir = extract_to / program_name

        if target_dir.exists():
            # Add suffix if folder already exists
            counter = 1
            while (extract_to / f"{program_name}_{counter}").exists():
                counter += 1
            target_dir = extract_to / f"{program_name}_{counter}"

        # Extract ZIP with safety checks
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                # Check for zip bombs (files that expand to huge sizes)
                total_size = sum(info.file_size for info in zip_ref.infolist())
                if total_size > 1024 * 1024 * 1024:  # 1GB limit
                    print(f"⚠ ZIP file too large (>1GB): {zip_path}")
                    return None

                zip_ref.extractall(target_dir)
                print(f"✓ Extracted ZIP to: {target_dir}")
        except zipfile.BadZipFile:
            print(f"✗ Corrupted ZIP file: {zip_path}")
            return None
        except Exception as e:
            print(f"✗ Failed to extract ZIP {zip_path}: {e}")
            return None

        # Scan the extracted folder
        bundles = scan_repository_folder(str(target_dir.parent), set())

        # Return the first bundle that matches the extracted folder
        for bundle in bundles:
            if target_dir.name in bundle.service.working_directory:
                return bundle

        # If no direct match, check if program is in a subdirectory
        bundles = scan_repository_folder(str(target_dir), set())
        if bundles:
            return bundles[0]

        print(f"⚠ No valid program found in ZIP: {zip_path.name}")
        return None

    except Exception as e:
        print(f"✗ Error extracting {zip_path}: {e}")
        return None
