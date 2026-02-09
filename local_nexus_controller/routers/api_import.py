from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends
from fastapi import HTTPException
from sqlmodel import Session, select
from sqlmodel import SQLModel

from local_nexus_controller.db import get_session
from local_nexus_controller.models import ImportBundle, KeyRef, Service, ServiceCreate
from local_nexus_controller.security import require_token
from local_nexus_controller.services.registry_import import import_bundle as import_bundle_impl


router = APIRouter()


class ScanBundlesRequest(SQLModel):
    """
    Scan a local folder for `local-nexus.bundle.json` files and import each bundle.

    Intended for bulk-importing many local Git repositories at once.
    """

    root: str
    bundle_filename: str = "local-nexus.bundle.json"
    max_files: int = 250
    include_git_repos: bool = True
    max_repos: int = 500
    dry_run: bool = False


class GitHubImportRequest(SQLModel):
    """
    Import a `local-nexus.bundle.json` directly from GitHub.

    Supports:
    - repo: "owner/repo" or "https://github.com/owner/repo"
    - file URL: "https://github.com/owner/repo/blob/<ref>/<path>" (ref+path auto-detected)
    """

    repo: str
    ref: str = "main"
    path: str = "local-nexus.bundle.json"
    github_token: str | None = None


class GitHubReposRequest(SQLModel):
    github_token: str | None = None
    per_page: int = 100
    max_pages: int = 5


class GitHubRepo(SQLModel):
    full_name: str
    html_url: str
    default_branch: str | None = None
    private: bool = False
    archived: bool = False
    description: str | None = None


class GitHubCreateBundlePrRequest(SQLModel):
    repo: str
    ref: str = "main"
    path: str = "local-nexus.bundle.json"
    github_token: str | None = None
    # Flag for the generated bundle metadata (signals "needs local work" in UI).
    needs_local_setup: bool = True


class GitHubLocalizePrRequest(SQLModel):
    repo: str
    ref: str = "main"
    path: str = "local-nexus.bundle.json"
    github_token: str | None = None
    needs_local_setup: bool = True
    scripts_dir: str = "tools/local-nexus"


class GitHubMergeReposPrRequest(SQLModel):
    """
    Create a PR in a destination repo that copies the source repo content into a subfolder.

    This copies files (no git history) using the GitHub Git Data API.
    """

    source_repo: str
    source_ref: str = "main"
    dest_repo: str
    dest_base: str | None = None  # default branch if omitted
    dest_subdir: str = ""  # default: merged/<sourceRepoName>
    github_token: str | None = None
    max_files: int = 250
    max_total_bytes: int = 15_000_000


class GitHubWorkspacePrepareRequest(SQLModel):
    repo: str
    branch: str
    github_token: str | None = None


class GitHubWorkspaceOpenRequest(SQLModel):
    workspace_path: str


class GitHubWorkspacePushRequest(SQLModel):
    workspace_path: str
    branch: str
    github_token: str | None = None
    commit_message: str = "Fix after merge/localize in Cursor"


class GitHubListBundlesRequest(SQLModel):
    repo: str
    ref: str = "main"
    github_token: str | None = None


class GitHubDeviceStartRequest(SQLModel):
    scope: str = "repo"


class GitHubDevicePollRequest(SQLModel):
    device_code: str


def _parse_github_input(repo_input: str, ref: str, path: str) -> tuple[str, str, str, str]:
    raw = (repo_input or "").strip()
    if not raw:
        raise HTTPException(status_code=400, detail="GitHub repo is required (e.g. owner/repo).")

    # owner/repo shorthand
    m = re.match(r"^([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)$", raw)
    if m:
        owner, repo = m.group(1), m.group(2)
        return owner, repo.removesuffix(".git"), (ref or "main").strip(), (path or "local-nexus.bundle.json").lstrip("/")

    # URL forms
    try:
        u = urllib.parse.urlparse(raw)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid GitHub URL/repo format.")

    host = (u.netloc or "").lower()
    parts = [p for p in (u.path or "").split("/") if p]

    if host in {"github.com", "www.github.com"} and len(parts) >= 2:
        owner, repo = parts[0], parts[1].removesuffix(".git")
        # https://github.com/owner/repo/blob/<ref>/<path...>
        if len(parts) >= 5 and parts[2] == "blob":
            ref_from_url = parts[3]
            path_from_url = "/".join(parts[4:])
            return owner, repo, ref_from_url, path_from_url
        return owner, repo, (ref or "main").strip(), (path or "local-nexus.bundle.json").lstrip("/")

    raise HTTPException(status_code=400, detail="Unsupported GitHub URL. Use owner/repo or a github.com URL.")


def _http_get_json_any(url: str, headers: dict[str, str]) -> object:
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310 - controlled URLs
            data = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        raise HTTPException(status_code=400, detail=f"GitHub request failed ({e.code}): {body or e.reason}")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"GitHub request failed: {e}")

    try:
        return json.loads(data)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"GitHub returned invalid JSON: {e}")


def _http_get_json(url: str, headers: dict[str, str]) -> dict:
    payload = _http_get_json_any(url, headers=headers)
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="GitHub returned an unexpected response.")
    return payload


def _http_get_text(url: str, headers: dict[str, str]) -> str:
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310 - controlled URLs
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        raise HTTPException(status_code=400, detail=f"GitHub request failed ({e.code}): {body or e.reason}")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"GitHub request failed: {e}")


def _fetch_bundle_json_from_github(owner: str, repo: str, ref: str, path: str, github_token: str | None) -> dict:
    # Prefer GitHub Contents API (supports private repos with token).
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{urllib.parse.quote(path)}?ref={urllib.parse.quote(ref)}"
    headers = {
        "User-Agent": "LocalNexusController",
        "Accept": "application/vnd.github+json",
    }
    if github_token and github_token.strip():
        headers["Authorization"] = f"Bearer {github_token.strip()}"

    try:
        payload = _http_get_json(api_url, headers=headers)
        if isinstance(payload, dict) and payload.get("type") == "file" and payload.get("content"):
            content_b64 = str(payload["content"]).replace("\n", "")
            try:
                raw = base64.b64decode(content_b64).decode("utf-8", errors="replace")
            except Exception as e:  # noqa: BLE001
                raise HTTPException(status_code=400, detail=f"Failed to decode bundle from GitHub: {e}")
            try:
                return json.loads(raw)
            except Exception as e:  # noqa: BLE001
                raise HTTPException(status_code=400, detail=f"Bundle file is not valid JSON: {e}")
    except HTTPException:
        # Fall through to raw URL below for public repos / rate-limit edge cases.
        pass

    raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}"
    text = _http_get_text(raw_url, headers={"User-Agent": "LocalNexusController"})
    try:
        return json.loads(text)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Bundle file is not valid JSON: {e}")


def _github_api_request(method: str, url: str, github_token: str, body: dict | None = None) -> Any:
    headers = {
        "User-Agent": "LocalNexusController",
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {github_token}",
    }
    data: bytes | None = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, headers=headers, method=method, data=data)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:  # noqa: S310 - controlled URLs
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        try:
            err = e.read().decode("utf-8", errors="replace")
        except Exception:
            err = ""
        raise HTTPException(status_code=400, detail=f"GitHub API error ({e.code}): {err or e.reason}")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"GitHub API request failed: {e}")

    if not raw.strip():
        return None
    try:
        return json.loads(raw)
    except Exception:
        return {"raw": raw}


def _github_oauth_client_id() -> str:
    client_id = (os.getenv("LOCAL_NEXUS_GITHUB_OAUTH_CLIENT_ID") or "").strip()
    if not client_id:
        raise HTTPException(
            status_code=400,
            detail="GitHub OAuth client_id missing. Set LOCAL_NEXUS_GITHUB_OAUTH_CLIENT_ID in your .env to use mobile auth.",
        )
    return client_id


def _github_device_start(scope: str) -> dict:
    client_id = _github_oauth_client_id()
    body = urllib.parse.urlencode({"client_id": client_id, "scope": scope or "repo"}).encode("utf-8")
    req = urllib.request.Request(
        "https://github.com/login/device/code",
        data=body,
        method="POST",
        headers={"Accept": "application/json", "User-Agent": "LocalNexusController", "Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:  # noqa: S310
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        try:
            err = e.read().decode("utf-8", errors="replace")
        except Exception:
            err = ""
        raise HTTPException(status_code=400, detail=f"GitHub device auth start failed ({e.code}): {err or e.reason}")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"GitHub device auth start failed: {e}")

    try:
        payload = json.loads(raw)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"GitHub device auth returned invalid JSON: {e}")
    if not isinstance(payload, dict) or not payload.get("device_code") or not payload.get("user_code"):
        raise HTTPException(status_code=400, detail="GitHub device auth returned an unexpected response.")
    return payload


def _github_device_poll(device_code: str) -> dict:
    client_id = _github_oauth_client_id()
    body = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://github.com/login/oauth/access_token",
        data=body,
        method="POST",
        headers={"Accept": "application/json", "User-Agent": "LocalNexusController", "Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:  # noqa: S310
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        try:
            err = e.read().decode("utf-8", errors="replace")
        except Exception:
            err = ""
        raise HTTPException(status_code=400, detail=f"GitHub device auth poll failed ({e.code}): {err or e.reason}")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"GitHub device auth poll failed: {e}")

    try:
        payload = json.loads(raw)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"GitHub token response invalid JSON: {e}")
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="GitHub token response unexpected.")
    return payload


def _default_bundle_for_repo(repo_full_name: str, needs_local_setup: bool) -> dict:
    # Minimal "starter" bundle. The user can refine commands/paths later.
    service_name = repo_full_name.split("/")[-1] if repo_full_name else "repo"
    return {
        "service": {
            "name": service_name,
            "description": f"Imported from GitHub repo {repo_full_name}",
            "category": "repos",
            "tags": ["github"],
            "tech_stack": ["git"],
            "dependencies": [],
            "config_paths": [],
            "port": None,
            "local_url": None,
            "healthcheck_url": None,
            # Intentionally blank: this depends on where the repo is cloned locally.
            "working_directory": "",
            "start_command": "",
            "stop_command": "",
            "restart_command": "",
            "env_overrides": {},
            "database_id": None,
            "database_connection_string": None,
            "database_schema_overview": None,
        },
        "database": None,
        "keys": [],
        "requested_port": None,
        "auto_assign_port": False,
        "auto_create_db": False,
        "meta": {
            "source": "github",
            "repo": repo_full_name,
            "needs_local_setup": bool(needs_local_setup),
            "notes": "Fill in working_directory + start_command for local runs. Then import this bundle.",
        },
    }


def _github_get_contents_meta(owner: str, repo: str, path: str, ref: str, token: str) -> dict | None:
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{urllib.parse.quote(path)}?ref={urllib.parse.quote(ref)}"
    try:
        payload = _github_api_request("GET", url, token)
    except HTTPException:
        return None
    return payload if isinstance(payload, dict) else None


def _github_get_file_text(owner: str, repo: str, path: str, ref: str, token: str) -> str | None:
    meta = _github_get_contents_meta(owner, repo, path, ref, token)
    if not meta or meta.get("type") != "file" or not meta.get("content"):
        return None
    content_b64 = str(meta["content"]).replace("\n", "")
    try:
        return base64.b64decode(content_b64).decode("utf-8", errors="replace")
    except Exception:
        return None


def _github_put_file(
    owner: str,
    repo: str,
    path: str,
    branch: str,
    message: str,
    content_text: str,
    token: str,
    sha: str | None = None,
) -> dict:
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{urllib.parse.quote(path)}"
    body: dict[str, Any] = {
        "message": message,
        "content": base64.b64encode(content_text.encode("utf-8")).decode("utf-8"),
        "branch": branch,
    }
    if sha:
        body["sha"] = sha
    res = _github_api_request("PUT", url, token, body=body)
    if not isinstance(res, dict):
        raise HTTPException(status_code=400, detail="GitHub returned an unexpected response while writing a file.")
    return res


def _github_list_repo_paths(owner: str, repo: str, ref: str, token: str) -> list[str]:
    # Resolve commit SHA for ref, then fetch tree recursively.
    ref_info = _github_api_request("GET", f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{urllib.parse.quote(ref)}", token)
    if not isinstance(ref_info, dict) or "object" not in ref_info:
        # If ref is not a branch, try tag refs.
        ref_info = _github_api_request("GET", f"https://api.github.com/repos/{owner}/{repo}/git/ref/tags/{urllib.parse.quote(ref)}", token)
    if not isinstance(ref_info, dict) or "object" not in ref_info:
        raise HTTPException(status_code=400, detail=f"Could not resolve ref: {ref}")

    sha = str((ref_info.get("object") or {}).get("sha") or "")
    if not sha:
        raise HTTPException(status_code=400, detail=f"Could not resolve ref SHA: {ref}")

    commit = _github_api_request("GET", f"https://api.github.com/repos/{owner}/{repo}/git/commits/{urllib.parse.quote(sha)}", token)
    if not isinstance(commit, dict):
        raise HTTPException(status_code=400, detail="Could not fetch commit info from GitHub.")
    tree_sha = str(((commit.get("tree") or {}) if isinstance(commit.get("tree"), dict) else {}).get("sha") or "")
    if not tree_sha:
        raise HTTPException(status_code=400, detail="Could not resolve tree SHA from GitHub.")

    tree = _github_api_request(
        "GET",
        f"https://api.github.com/repos/{owner}/{repo}/git/trees/{urllib.parse.quote(tree_sha)}?recursive=1",
        token,
    )
    if not isinstance(tree, dict) or "tree" not in tree:
        raise HTTPException(status_code=400, detail="Could not list repo tree from GitHub.")

    paths: list[str] = []
    for item in tree.get("tree") or []:
        if not isinstance(item, dict):
            continue
        if item.get("type") != "blob":
            continue
        p = str(item.get("path") or "")
        if p:
            paths.append(p)
    return paths


def _github_get_tree_entries(owner: str, repo: str, ref: str, token: str) -> list[dict]:
    # Resolve commit SHA for ref, then fetch tree recursively and return entries.
    ref_info = _github_api_request("GET", f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{urllib.parse.quote(ref)}", token)
    if not isinstance(ref_info, dict) or "object" not in ref_info:
        ref_info = _github_api_request("GET", f"https://api.github.com/repos/{owner}/{repo}/git/ref/tags/{urllib.parse.quote(ref)}", token)
    if not isinstance(ref_info, dict) or "object" not in ref_info:
        raise HTTPException(status_code=400, detail=f"Could not resolve ref: {ref}")

    sha = str((ref_info.get("object") or {}).get("sha") or "")
    if not sha:
        raise HTTPException(status_code=400, detail=f"Could not resolve ref SHA: {ref}")

    commit = _github_api_request("GET", f"https://api.github.com/repos/{owner}/{repo}/git/commits/{urllib.parse.quote(sha)}", token)
    if not isinstance(commit, dict):
        raise HTTPException(status_code=400, detail="Could not fetch commit info from GitHub.")
    tree_sha = str(((commit.get("tree") or {}) if isinstance(commit.get("tree"), dict) else {}).get("sha") or "")
    if not tree_sha:
        raise HTTPException(status_code=400, detail="Could not resolve tree SHA from GitHub.")

    tree = _github_api_request(
        "GET",
        f"https://api.github.com/repos/{owner}/{repo}/git/trees/{urllib.parse.quote(tree_sha)}?recursive=1",
        token,
    )
    if not isinstance(tree, dict) or "tree" not in tree:
        raise HTTPException(status_code=400, detail="Could not list repo tree from GitHub.")

    entries = tree.get("tree") or []
    if not isinstance(entries, list):
        return []
    return [e for e in entries if isinstance(e, dict)]


def _github_get_blob(owner: str, repo: str, sha: str, token: str) -> dict:
    blob = _github_api_request("GET", f"https://api.github.com/repos/{owner}/{repo}/git/blobs/{urllib.parse.quote(sha)}", token)
    if not isinstance(blob, dict) or "content" not in blob:
        raise HTTPException(status_code=400, detail="GitHub returned an unexpected blob response.")
    return blob


def _github_create_blob(dest_owner: str, dest_repo: str, content_b64: str, token: str) -> str:
    res = _github_api_request(
        "POST",
        f"https://api.github.com/repos/{dest_owner}/{dest_repo}/git/blobs",
        token,
        body={"content": content_b64.replace("\n", ""), "encoding": "base64"},
    )
    if not isinstance(res, dict) or not res.get("sha"):
        raise HTTPException(status_code=400, detail="Failed to create blob in destination repo.")
    return str(res["sha"])


def _github_create_tree(dest_owner: str, dest_repo: str, base_tree_sha: str, items: list[dict[str, Any]], token: str) -> str:
    res = _github_api_request(
        "POST",
        f"https://api.github.com/repos/{dest_owner}/{dest_repo}/git/trees",
        token,
        body={"base_tree": base_tree_sha, "tree": items},
    )
    if not isinstance(res, dict) or not res.get("sha"):
        raise HTTPException(status_code=400, detail="Failed to create tree in destination repo.")
    return str(res["sha"])


def _github_create_commit(dest_owner: str, dest_repo: str, message: str, tree_sha: str, parent_sha: str, token: str) -> str:
    res = _github_api_request(
        "POST",
        f"https://api.github.com/repos/{dest_owner}/{dest_repo}/git/commits",
        token,
        body={"message": message, "tree": tree_sha, "parents": [parent_sha]},
    )
    if not isinstance(res, dict) or not res.get("sha"):
        raise HTTPException(status_code=400, detail="Failed to create commit in destination repo.")
    return str(res["sha"])


def _github_update_ref(dest_owner: str, dest_repo: str, branch: str, sha: str, token: str) -> None:
    _github_api_request(
        "PATCH",
        f"https://api.github.com/repos/{dest_owner}/{dest_repo}/git/refs/heads/{urllib.parse.quote(branch)}",
        token,
        body={"sha": sha, "force": False},
    )


def _safe_workspace_name(owner: str, repo: str, branch: str) -> str:
    raw = f"{owner}__{repo}__{branch}"
    return "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in raw)[:160]


def _run_git(cmd: list[str], cwd: Path, token: str | None = None, timeout_s: int = 300) -> tuple[int, str]:
    env = os.environ.copy()
    full_cmd = ["git"]
    if token:
        # Avoid storing token in remote URL; send as header for this command.
        full_cmd += ["-c", f"http.extraHeader=AUTHORIZATION: bearer {token}"]
    full_cmd += cmd
    try:
        res = subprocess.run(
            full_cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout_s,
            shell=False,
            env=env,
        )
        out = (res.stdout or "") + ("\n" + res.stderr if res.stderr else "")
        return int(res.returncode), out.strip()
    except FileNotFoundError:
        raise HTTPException(status_code=400, detail="git not found on PATH. Install Git for Windows.")
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=400, detail=f"git command timed out: {' '.join(cmd)}")


def _find_cursor_command() -> list[str] | None:
    # Prefer CLI "cursor" if installed.
    from shutil import which

    c = which("cursor")
    if c:
        return [c]
    # Common Windows install paths (best-effort).
    candidates = [
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Cursor", "Cursor.exe"),
        os.path.join(os.environ.get("PROGRAMFILES", ""), "Cursor", "Cursor.exe"),
        os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "Cursor", "Cursor.exe"),
    ]
    for p in candidates:
        if p and Path(p).exists():
            return [p]
    return None


def _detect_local_run_config(
    owner: str,
    repo: str,
    ref: str,
    token: str,
) -> dict:
    paths = _github_list_repo_paths(owner, repo, ref, token)
    s = set(paths)

    detected: list[str] = []
    docker_compose = next((p for p in ["docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"] if p in s), None)
    dockerfile = "Dockerfile" if "Dockerfile" in s else None
    if docker_compose or dockerfile:
        detected.append("docker")

    package_json_text = _github_get_file_text(owner, repo, "package.json", ref, token) if "package.json" in s else None
    package_json: dict | None = None
    node_entry = None
    node_script = None
    if package_json_text:
        try:
            package_json = json.loads(package_json_text)
        except Exception:
            package_json = None
    if package_json:
        detected.append("node")
        scripts = package_json.get("scripts") if isinstance(package_json.get("scripts"), dict) else {}
        if isinstance(scripts, dict):
            if "dev" in scripts:
                node_script = "dev"
            elif "start" in scripts:
                node_script = "start"
        if not node_script:
            node_entry = str(package_json.get("main") or "").strip() or None

    csproj_paths = [p for p in paths if p.lower().endswith((".csproj", ".fsproj", ".vbproj"))]
    sln_paths = [p for p in paths if p.lower().endswith(".sln")]
    dotnet_project = None
    if csproj_paths or sln_paths:
        detected.append("dotnet")
        # Prefer a web SDK project if we can detect it quickly.
        web_candidate = None
        for p in csproj_paths[:20]:
            txt = _github_get_file_text(owner, repo, p, ref, token)
            if txt and ("Microsoft.NET.Sdk.Web" in txt):
                web_candidate = p
                break
        dotnet_project = web_candidate or (csproj_paths[0] if csproj_paths else sln_paths[0])

    python_markers = any(p in s for p in ["pyproject.toml", "requirements.txt", "setup.py", "Pipfile"])
    python_entry = None
    if python_markers or any(p.lower().endswith(".py") for p in paths[:200]):
        # Heuristic: pick a likely entrypoint.
        for cand in [
            "main.py",
            "app/main.py",
            "src/main.py",
            "server.py",
            "api/main.py",
            "manage.py",
        ]:
            if cand in s:
                python_entry = cand
                break
        if python_markers:
            detected.append("python")

    # De-dupe & order.
    order = ["docker", "dotnet", "node", "python"]
    detected = [x for x in order if x in detected]

    return {
        "detected": detected,
        "docker_compose": docker_compose,
        "dockerfile": dockerfile,
        "node_script": node_script,
        "node_entry": node_entry,
        "dotnet_project": dotnet_project,
        "python_entry": python_entry,
        "has_pyproject": "pyproject.toml" in s,
        "has_requirements": "requirements.txt" in s,
    }


def _generate_local_nexus_start_ps1(cfg: dict) -> str:
    docker_compose = cfg.get("docker_compose")
    dotnet_project = cfg.get("dotnet_project")
    node_script = cfg.get("node_script")
    node_entry = cfg.get("node_entry")
    python_entry = cfg.get("python_entry")
    has_requirements = bool(cfg.get("has_requirements"))
    has_pyproject = bool(cfg.get("has_pyproject"))

    lines: list[str] = []
    lines.append('$ErrorActionPreference = "Stop"')
    lines.append("")
    lines.append("# Auto-generated by Local Nexus Controller")
    lines.append("# Runs this repo locally (best-effort) for Python/Node/Docker/.NET.")
    lines.append("")
    lines.append('$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\\..")).Path')
    lines.append("Set-Location $repoRoot")
    lines.append("")
    lines.append("Write-Host \"Repo root: $repoRoot\"")
    lines.append("")
    if docker_compose:
        lines.append("# Docker Compose detected")
        lines.append('Write-Host "Starting via docker compose..."')
        lines.append("docker compose up -d")
        lines.append("exit 0")
        lines.append("")
    if dotnet_project:
        lines.append("# .NET detected")
        lines.append(f'$dotnetProject = "{dotnet_project}"')
        lines.append('Write-Host "Starting via dotnet..."')
        lines.append("dotnet restore")
        lines.append("dotnet run --project $dotnetProject")
        lines.append("exit 0")
        lines.append("")
    if node_script or node_entry:
        lines.append("# Node detected")
        lines.append('Write-Host "Starting via Node..."')
        lines.append("npm install")
        if node_script:
            lines.append(f'npm run {node_script}')
        elif node_entry:
            lines.append(f'node "{node_entry}"')
        else:
            lines.append("npm start")
        lines.append("exit 0")
        lines.append("")
    if python_entry or has_requirements or has_pyproject:
        lines.append("# Python detected")
        lines.append('Write-Host "Starting via Python..."')
        lines.append('$venvPy = Join-Path $repoRoot ".venv\\Scripts\\python.exe"')
        lines.append('if (!(Test-Path $venvPy)) { py -m venv .venv }')
        lines.append('$venvPy = Join-Path $repoRoot ".venv\\Scripts\\python.exe"')
        if has_requirements:
            lines.append('& $venvPy -m pip install -r "requirements.txt"')
        elif has_pyproject:
            lines.append('& $venvPy -m pip install -e .')
        else:
            lines.append('# No requirements.txt/pyproject.toml detected; skipping install.')
        if python_entry:
            lines.append(f'& $venvPy "{python_entry}"')
            lines.append("exit 0")
        else:
            lines.append('throw "Python project detected but no entrypoint found. Edit this script or set start_command in the bundle."')
        lines.append("")

    lines.append('throw "No supported local run configuration detected. Add Docker/.NET/Node/Python config and retry."')
    lines.append("")
    return "\n".join(lines) + "\n"


def _generate_local_nexus_stop_ps1(cfg: dict) -> str:
    docker_compose = cfg.get("docker_compose")
    lines: list[str] = []
    lines.append('$ErrorActionPreference = "Stop"')
    lines.append("")
    lines.append("# Auto-generated by Local Nexus Controller")
    lines.append("")
    lines.append('$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\\..")).Path')
    lines.append("Set-Location $repoRoot")
    lines.append("")
    if docker_compose:
        lines.append('Write-Host "Stopping via docker compose..."')
        lines.append("docker compose down")
        lines.append("exit 0")
    lines.append('Write-Host "Stop not implemented for this repo type (no docker compose detected)."')
    lines.append("exit 0")
    lines.append("")
    return "\n".join(lines) + "\n"


@router.post("/bundle", dependencies=[Depends(require_token)])
def import_bundle(bundle: ImportBundle, session: Session = Depends(get_session)) -> dict:
    res = import_bundle_impl(session, bundle)
    return {"service_id": res.service_id, "database_id": res.database_id, "warnings": res.warnings}


@router.post("/github-bundle", dependencies=[Depends(require_token)])
def import_github_bundle(req: GitHubImportRequest, session: Session = Depends(get_session)) -> dict:
    owner, repo, ref, path = _parse_github_input(req.repo, req.ref, req.path)
    payload = _fetch_bundle_json_from_github(owner, repo, ref, path, req.github_token)
    try:
        bundle = ImportBundle.model_validate(payload)  # type: ignore[attr-defined]
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Bundle JSON failed validation: {e}")

    res = import_bundle_impl(session, bundle)
    return {
        "source": "github",
        "owner": owner,
        "repo": repo,
        "ref": ref,
        "path": path,
        "service_id": res.service_id,
        "database_id": res.database_id,
        "warnings": res.warnings,
    }


@router.post("/github-repos", dependencies=[Depends(require_token)])
def list_github_repos(req: GitHubReposRequest) -> dict:
    token = (req.github_token or "").strip()
    if not token:
        raise HTTPException(status_code=400, detail="GitHub token required. Click 'GitHub token' and paste one.")

    per_page = int(req.per_page or 100)
    per_page = max(10, min(per_page, 100))
    max_pages = int(req.max_pages or 5)
    max_pages = max(1, min(max_pages, 10))

    headers = {
        "User-Agent": "LocalNexusController",
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
    }

    repos: list[GitHubRepo] = []
    # Use the authenticated user's visible repos (including org/collab) via affiliations.
    # https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#list-repositories-for-the-authenticated-user
    for page in range(1, max_pages + 1):
        url = (
            "https://api.github.com/user/repos"
            f"?per_page={per_page}&page={page}&sort=updated&direction=desc&affiliation=owner,collaborator,organization_member"
        )
        payload = _http_get_json_any(url, headers=headers)
        if not isinstance(payload, list):
            raise HTTPException(status_code=400, detail="GitHub returned an unexpected response while listing repos.")
        if not payload:
            break

        for r in payload:
            if not isinstance(r, dict):
                continue
            repos.append(
                GitHubRepo(
                    full_name=str(r.get("full_name") or ""),
                    html_url=str(r.get("html_url") or ""),
                    default_branch=(str(r.get("default_branch")) if r.get("default_branch") else None),
                    private=bool(r.get("private") or False),
                    archived=bool(r.get("archived") or False),
                    description=(str(r.get("description")) if r.get("description") else None),
                )
            )

        if len(payload) < per_page:
            break

    repos = [r for r in repos if r.full_name]
    return {"count": len(repos), "repos": [r.model_dump() for r in repos]}  # type: ignore[attr-defined]


@router.post("/github-create-bundle-pr", dependencies=[Depends(require_token)])
def github_create_bundle_pr(req: GitHubCreateBundlePrRequest) -> dict:
    token = (req.github_token or "").strip()
    if not token:
        raise HTTPException(status_code=400, detail="GitHub token required. Click 'GitHub token' and paste one.")

    owner, repo, ref, path = _parse_github_input(req.repo, req.ref, req.path)
    repo_full_name = f"{owner}/{repo}"

    # Get repo info (default branch).
    repo_info = _github_api_request("GET", f"https://api.github.com/repos/{owner}/{repo}", token)
    if not isinstance(repo_info, dict):
        raise HTTPException(status_code=400, detail="GitHub returned unexpected repo info.")
    base_branch = str(repo_info.get("default_branch") or ref or "main")

    # If file already exists on base branch, do nothing.
    contents_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{urllib.parse.quote(path)}?ref={urllib.parse.quote(base_branch)}"
    try:
        existing = _github_api_request("GET", contents_url, token)
        if isinstance(existing, dict) and existing.get("type") == "file":
            return {
                "status": "exists",
                "message": f"{path} already exists on {repo_full_name}@{base_branch}.",
                "repo": repo_full_name,
                "base": base_branch,
                "path": path,
            }
    except HTTPException:
        # 404 will be surfaced as 400 by our wrapper; treat as "not found" and continue.
        pass

    branch_name = f"local-nexus/add-bundle-{Path(path).stem}".replace("..", ".")

    # Create a new branch from base.
    ref_info = _github_api_request("GET", f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{urllib.parse.quote(base_branch)}", token)
    if not isinstance(ref_info, dict) or "object" not in ref_info:
        raise HTTPException(status_code=400, detail="Could not resolve base branch SHA.")
    base_sha = str((ref_info.get("object") or {}).get("sha") or "")
    if not base_sha:
        raise HTTPException(status_code=400, detail="Could not resolve base branch SHA.")

    # Create ref (ignore if it already exists).
    try:
        _github_api_request(
            "POST",
            f"https://api.github.com/repos/{owner}/{repo}/git/refs",
            token,
            body={"ref": f"refs/heads/{branch_name}", "sha": base_sha},
        )
    except HTTPException:
        # Branch may already exist from a previous run; continue.
        pass

    bundle_payload = _default_bundle_for_repo(repo_full_name, needs_local_setup=bool(req.needs_local_setup))
    content_b64 = base64.b64encode(json.dumps(bundle_payload, indent=2).encode("utf-8")).decode("utf-8")

    # Create the file on the new branch.
    put_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{urllib.parse.quote(path)}"
    put_body = {
        "message": f"Add {path} for Local Nexus import",
        "content": content_b64,
        "branch": branch_name,
    }
    _github_api_request("PUT", put_url, token, body=put_body)

    # Open a PR.
    pr_body = (
        "Adds `local-nexus.bundle.json` so Local Nexus Controller can import this repo.\n\n"
        "- Next steps: fill `service.working_directory` + `service.start_command` for your machine.\n"
        "- Then import via the dashboard Import tab.\n"
    )
    pr = _github_api_request(
        "POST",
        f"https://api.github.com/repos/{owner}/{repo}/pulls",
        token,
        body={"title": "Add Local Nexus bundle", "head": branch_name, "base": base_branch, "body": pr_body},
    )
    if not isinstance(pr, dict):
        raise HTTPException(status_code=400, detail="Failed to create PR (unexpected response).")

    return {
        "status": "created",
        "repo": repo_full_name,
        "base": base_branch,
        "branch": branch_name,
        "path": path,
        "pr_url": pr.get("html_url"),
        "message": "PR created. Merge it to add the bundle to the repo.",
    }


@router.post("/github-localize-pr", dependencies=[Depends(require_token)])
def github_localize_pr(req: GitHubLocalizePrRequest) -> dict:
    token = (req.github_token or "").strip()
    if not token:
        raise HTTPException(status_code=400, detail="GitHub token required. Click 'GitHub token' and paste one.")

    owner, repo, ref, bundle_path = _parse_github_input(req.repo, req.ref, req.path)
    repo_full_name = f"{owner}/{repo}"

    repo_info = _github_api_request("GET", f"https://api.github.com/repos/{owner}/{repo}", token)
    if not isinstance(repo_info, dict):
        raise HTTPException(status_code=400, detail="GitHub returned unexpected repo info.")
    base_branch = str(repo_info.get("default_branch") or ref or "main")

    cfg = _detect_local_run_config(owner, repo, base_branch, token)

    scripts_dir = (req.scripts_dir or "tools/local-nexus").strip().strip("/").strip()
    start_ps1_path = f"{scripts_dir}/start.ps1"
    stop_ps1_path = f"{scripts_dir}/stop.ps1"

    branch_name = f"local-nexus/localize-{repo}".replace("..", ".")

    # Create a new branch from base.
    ref_info = _github_api_request("GET", f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{urllib.parse.quote(base_branch)}", token)
    if not isinstance(ref_info, dict) or "object" not in ref_info:
        raise HTTPException(status_code=400, detail="Could not resolve base branch SHA.")
    base_sha = str((ref_info.get("object") or {}).get("sha") or "")
    if not base_sha:
        raise HTTPException(status_code=400, detail="Could not resolve base branch SHA.")

    try:
        _github_api_request(
            "POST",
            f"https://api.github.com/repos/{owner}/{repo}/git/refs",
            token,
            body={"ref": f"refs/heads/{branch_name}", "sha": base_sha},
        )
    except HTTPException:
        pass

    warnings: list[str] = []

    # Write start/stop scripts (skip if already exist).
    for pth, content, msg in [
        (start_ps1_path, _generate_local_nexus_start_ps1(cfg), f"Add {start_ps1_path}"),
        (stop_ps1_path, _generate_local_nexus_stop_ps1(cfg), f"Add {stop_ps1_path}"),
    ]:
        meta = _github_get_contents_meta(owner, repo, pth, branch_name, token)
        if meta and meta.get("sha"):
            warnings.append(f"Skipped existing file: {pth}")
            continue
        _github_put_file(owner, repo, pth, branch_name, msg, content, token)

    # Create or update bundle
    bundle_meta = _github_get_contents_meta(owner, repo, bundle_path, branch_name, token)
    bundle_existing_text = None
    bundle_existing_sha = None
    if bundle_meta and bundle_meta.get("sha"):
        bundle_existing_sha = str(bundle_meta.get("sha"))
        bundle_existing_text = _github_get_file_text(owner, repo, bundle_path, branch_name, token)

    bundle_payload: dict
    if bundle_existing_text:
        try:
            bundle_payload = json.loads(bundle_existing_text)
            if not isinstance(bundle_payload, dict):
                raise ValueError("Bundle is not a JSON object")
        except Exception as e:  # noqa: BLE001
            warnings.append(f"Existing bundle could not be parsed; overwriting: {e}")
            bundle_payload = _default_bundle_for_repo(repo_full_name, needs_local_setup=bool(req.needs_local_setup))
    else:
        bundle_payload = _default_bundle_for_repo(repo_full_name, needs_local_setup=bool(req.needs_local_setup))

    svc = bundle_payload.get("service") if isinstance(bundle_payload.get("service"), dict) else {}
    if isinstance(svc, dict):
        # Don't clobber user-provided values; only fill if blank.
        if not str(svc.get("working_directory") or "").strip():
            svc["working_directory"] = "{REPO_ROOT}"
        if not str(svc.get("start_command") or "").strip():
            svc["start_command"] = f"powershell -ExecutionPolicy Bypass -File {start_ps1_path.replace('/', '\\\\')}"
        if not str(svc.get("stop_command") or "").strip():
            svc["stop_command"] = f"powershell -ExecutionPolicy Bypass -File {stop_ps1_path.replace('/', '\\\\')}"

        tech = svc.get("tech_stack")
        if not isinstance(tech, list):
            tech = []
        detected = cfg.get("detected") or []
        if isinstance(detected, list):
            for t in detected:
                if t not in tech:
                    tech.append(t)
        if "git" not in tech:
            tech.append("git")
        svc["tech_stack"] = tech
        bundle_payload["service"] = svc

    meta = bundle_payload.get("meta") if isinstance(bundle_payload.get("meta"), dict) else {}
    if not isinstance(meta, dict):
        meta = {}
    meta.setdefault("source", "github")
    meta["repo"] = repo_full_name
    meta["needs_local_setup"] = bool(req.needs_local_setup)
    meta["local_nexus_scripts_dir"] = scripts_dir
    meta["detected_stacks"] = cfg.get("detected")
    meta["notes"] = (
        "Generated local run scripts for Cursor/Local Nexus. "
        "Set service.working_directory to your clone path (or replace {REPO_ROOT}) if needed."
    )
    bundle_payload["meta"] = meta

    bundle_text = json.dumps(bundle_payload, indent=2) + "\n"
    _github_put_file(
        owner,
        repo,
        bundle_path,
        branch_name,
        f"Add/update {bundle_path} for Local Nexus local runs",
        bundle_text,
        token,
        sha=bundle_existing_sha,
    )

    pr_body = (
        "Adds/updates Local Nexus files to run this repo locally.\n\n"
        f"Detected: {', '.join(cfg.get('detected') or []) or 'unknown'}\n\n"
        "- Adds `tools/local-nexus/start.ps1` (best-effort local runner)\n"
        "- Adds `tools/local-nexus/stop.ps1`\n"
        f"- Adds/updates `{bundle_path}` with start/stop commands\n\n"
        "After merge: clone the repo locally, set `working_directory` in the bundle to your clone path, then import."
    )
    pr = _github_api_request(
        "POST",
        f"https://api.github.com/repos/{owner}/{repo}/pulls",
        token,
        body={"title": "Localize repo for Local Nexus", "head": branch_name, "base": base_branch, "body": pr_body},
    )
    if not isinstance(pr, dict):
        raise HTTPException(status_code=400, detail="Failed to create PR (unexpected response).")

    return {
        "status": "created",
        "repo": repo_full_name,
        "base": base_branch,
        "branch": branch_name,
        "bundle_path": bundle_path,
        "scripts_dir": scripts_dir,
        "detected": cfg.get("detected"),
        "warnings": warnings,
        "pr_url": pr.get("html_url"),
        "message": "PR created. Merge it to add local run scripts + bundle updates.",
    }


@router.post("/github-merge-repos-pr", dependencies=[Depends(require_token)])
def github_merge_repos_pr(req: GitHubMergeReposPrRequest) -> dict:
    token = (req.github_token or "").strip()
    if not token:
        raise HTTPException(status_code=400, detail="GitHub token required. Click 'GitHub token' and paste one.")

    src_owner, src_repo, src_ref, _ = _parse_github_input(req.source_repo, req.source_ref, "x")
    dst_owner, dst_repo, _, _ = _parse_github_input(req.dest_repo, "main", "x")
    src_full = f"{src_owner}/{src_repo}"
    dst_full = f"{dst_owner}/{dst_repo}"

    dst_info = _github_api_request("GET", f"https://api.github.com/repos/{dst_owner}/{dst_repo}", token)
    if not isinstance(dst_info, dict):
        raise HTTPException(status_code=400, detail="GitHub returned unexpected destination repo info.")
    base_branch = str(req.dest_base or dst_info.get("default_branch") or "main")

    subdir = (req.dest_subdir or "").strip().strip("/").strip()
    if not subdir:
        # Preferred monorepo layout: apps/<name>
        subdir = f"apps/{src_repo}"
    if ".." in subdir.split("/"):
        raise HTTPException(status_code=400, detail="dest_subdir may not contain '..'")

    max_files = max(1, min(int(req.max_files or 250), 2000))
    max_total_bytes = max(100_000, min(int(req.max_total_bytes or 15_000_000), 200_000_000))

    base_ref = _github_api_request("GET", f"https://api.github.com/repos/{dst_owner}/{dst_repo}/git/ref/heads/{urllib.parse.quote(base_branch)}", token)
    if not isinstance(base_ref, dict) or "object" not in base_ref:
        raise HTTPException(status_code=400, detail="Could not resolve destination base branch SHA.")
    base_sha = str((base_ref.get("object") or {}).get("sha") or "")
    if not base_sha:
        raise HTTPException(status_code=400, detail="Could not resolve destination base branch SHA.")

    base_commit = _github_api_request("GET", f"https://api.github.com/repos/{dst_owner}/{dst_repo}/git/commits/{urllib.parse.quote(base_sha)}", token)
    if not isinstance(base_commit, dict):
        raise HTTPException(status_code=400, detail="Could not fetch destination base commit.")
    base_tree_sha = str(((base_commit.get("tree") or {}) if isinstance(base_commit.get("tree"), dict) else {}).get("sha") or "")
    if not base_tree_sha:
        raise HTTPException(status_code=400, detail="Could not resolve destination base tree SHA.")

    branch_name = f"local-nexus/merge-{src_repo}-into-{dst_repo}".replace("..", ".")
    try:
        _github_api_request(
            "POST",
            f"https://api.github.com/repos/{dst_owner}/{dst_repo}/git/refs",
            token,
            body={"ref": f"refs/heads/{branch_name}", "sha": base_sha},
        )
    except HTTPException:
        pass

    entries = _github_get_tree_entries(src_owner, src_repo, src_ref, token)
    blobs = [e for e in entries if e.get("type") == "blob" and e.get("path") and e.get("sha")]
    if not blobs:
        raise HTTPException(status_code=400, detail="No files found in source repo at that ref.")

    # Destination base paths (used to avoid overwriting common helper files we generate).
    dst_base_entries = _github_get_tree_entries(dst_owner, dst_repo, base_branch, token)
    dst_existing_paths = {str(e.get("path")) for e in dst_base_entries if e.get("type") == "blob" and e.get("path")}

    total_bytes = 0
    tree_items: list[dict[str, Any]] = []
    warnings: list[str] = []
    created_files = 0

    for e in blobs:
        if created_files >= max_files:
            warnings.append(f"Reached max_files={max_files}; remaining files not copied.")
            break

        src_path = str(e.get("path") or "")
        if not src_path or src_path.startswith(".git/"):
            continue

        src_sha = str(e.get("sha") or "")
        blob = _github_get_blob(src_owner, src_repo, src_sha, token)
        if bool(blob.get("truncated")):
            warnings.append(f"Skipped large file (truncated by GitHub API): {src_path}")
            continue
        size = int(blob.get("size") or 0)
        if total_bytes + size > max_total_bytes:
            warnings.append(f"Reached max_total_bytes={max_total_bytes}; remaining files not copied.")
            break

        if str(blob.get("encoding") or "base64") != "base64":
            warnings.append(f"Skipped file with unknown encoding: {src_path}")
            continue

        content_b64 = str(blob.get("content") or "")
        dest_blob_sha = _github_create_blob(dst_owner, dst_repo, content_b64, token)
        dest_path = f"{subdir}/{src_path}".replace("//", "/")
        tree_items.append({"path": dest_path, "mode": "100644", "type": "blob", "sha": dest_blob_sha})
        total_bytes += size
        created_files += 1

    # Add Local Nexus scripts for the merged app (best-effort) if not already present.
    try:
        cfg = _detect_local_run_config(src_owner, src_repo, src_ref, token)
        app_start_rel = f"{subdir}/tools/local-nexus/start.ps1"
        app_stop_rel = f"{subdir}/tools/local-nexus/stop.ps1"

        for rel_path, content_text, label in [
            (app_start_rel, _generate_local_nexus_start_ps1(cfg), "Add app start script"),
            (app_stop_rel, _generate_local_nexus_stop_ps1(cfg), "Add app stop script"),
        ]:
            # If the source repo already contained these paths, they were copied above; don't overwrite.
            if any(t.get("path") == rel_path for t in tree_items) or rel_path in dst_existing_paths:
                warnings.append(f"Skipped generating (already exists): {rel_path}")
                continue
            b64 = base64.b64encode(content_text.encode("utf-8")).decode("utf-8")
            sha = _github_create_blob(dst_owner, dst_repo, b64, token)
            tree_items.append({"path": rel_path, "mode": "100644", "type": "blob", "sha": sha})
    except Exception as e:  # noqa: BLE001
        warnings.append(f"Local Nexus app scripts not generated: {e}")

    # Add a simple root "master program" runner + helper scripts + master bundle (non-destructive filenames).
    master_scripts_dir = "tools/local-nexus"
    master_start = f"{master_scripts_dir}/start-all.ps1"
    master_stop = f"{master_scripts_dir}/stop-all.ps1"
    master_docker_up = f"{master_scripts_dir}/docker-up.ps1"
    master_docker_down = f"{master_scripts_dir}/docker-down.ps1"
    master_env_agg = f"{master_scripts_dir}/generate-env-example.ps1"
    master_port_check = f"{master_scripts_dir}/check-ports.ps1"
    master_bundle_path = "local-nexus.apps.bundle.json"

    dest_has_root_start = "tools/local-nexus/start.ps1" in dst_existing_paths
    dest_has_root_stop = "tools/local-nexus/stop.ps1" in dst_existing_paths

    master_start_lines: list[str] = []
    master_start_lines.append('$ErrorActionPreference = "Stop"')
    master_start_lines.append("")
    master_start_lines.append("# Auto-generated by Local Nexus Controller")
    master_start_lines.append("# Starts the 'master program' (destination root + every app under apps/*).")
    master_start_lines.append("")
    master_start_lines.append('$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot \"..\\..\" )).Path')
    master_start_lines.append("Set-Location $repoRoot")
    master_start_lines.append("")
    if dest_has_root_start:
        master_start_lines.append('Write-Host \"Starting destination root service...\"')
        master_start_lines.append('powershell -ExecutionPolicy Bypass -File \"tools\\local-nexus\\start.ps1\"')
        master_start_lines.append("")
    master_start_lines.append('Write-Host \"Starting apps/* ...\"')
    master_start_lines.append('$appsRoot = Join-Path $repoRoot "apps"')
    master_start_lines.append('if (!(Test-Path $appsRoot)) { Write-Host "No apps/ folder found."; exit 0 }')
    master_start_lines.append('$apps = Get-ChildItem -Path $appsRoot -Directory -ErrorAction SilentlyContinue')
    master_start_lines.append("foreach ($app in $apps) {")
    master_start_lines.append('  $appRoot = $app.FullName')
    master_start_lines.append('  $rel = Join-Path "apps" $app.Name')
    master_start_lines.append('  $startScript = Join-Path $appRoot "tools\\local-nexus\\start.ps1"')
    master_start_lines.append("  if (Test-Path $startScript) {")
    master_start_lines.append('    Write-Host ("Starting " + $rel)')
    master_start_lines.append('    powershell -ExecutionPolicy Bypass -File $startScript')
    master_start_lines.append("    continue")
    master_start_lines.append("  }")
    master_start_lines.append("  # Fallback: if the app has a compose file, start it with an isolated project name.")
    master_start_lines.append('  $composeCandidates = @("docker-compose.yml","docker-compose.yaml","compose.yml","compose.yaml")')
    master_start_lines.append('  $compose = $composeCandidates | ForEach-Object { Join-Path $appRoot $_ } | Where-Object { Test-Path $_ } | Select-Object -First 1')
    master_start_lines.append("  if ($compose) {")
    master_start_lines.append('    $project = ("lnc-" + $app.Name).ToLowerInvariant()')
    master_start_lines.append('    Write-Host ("Starting docker compose for " + $rel + " (project " + $project + ")")')
    master_start_lines.append('    docker compose -f $compose -p $project up -d')
    master_start_lines.append("    continue")
    master_start_lines.append("  }")
    master_start_lines.append('  Write-Host ("No start script or compose file for " + $rel + ". Run Localize PR for that app.")')
    master_start_lines.append("}")
    master_start_text = "\n".join(master_start_lines) + "\n"

    master_stop_lines: list[str] = []
    master_stop_lines.append('$ErrorActionPreference = "Stop"')
    master_stop_lines.append("")
    master_stop_lines.append("# Auto-generated by Local Nexus Controller")
    master_stop_lines.append("")
    master_stop_lines.append('$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot \"..\\..\" )).Path')
    master_stop_lines.append("Set-Location $repoRoot")
    master_stop_lines.append("")
    if dest_has_root_stop:
        master_stop_lines.append('Write-Host \"Stopping destination root service...\"')
        master_stop_lines.append('powershell -ExecutionPolicy Bypass -File \"tools\\local-nexus\\stop.ps1\"')
        master_stop_lines.append("")
    master_stop_lines.append('Write-Host \"Stopping apps/* ...\"')
    master_stop_lines.append('$appsRoot = Join-Path $repoRoot "apps"')
    master_stop_lines.append('if (!(Test-Path $appsRoot)) { Write-Host "No apps/ folder found."; exit 0 }')
    master_stop_lines.append('$apps = Get-ChildItem -Path $appsRoot -Directory -ErrorAction SilentlyContinue')
    master_stop_lines.append("foreach ($app in $apps) {")
    master_stop_lines.append('  $appRoot = $app.FullName')
    master_stop_lines.append('  $rel = Join-Path "apps" $app.Name')
    master_stop_lines.append('  $stopScript = Join-Path $appRoot "tools\\local-nexus\\stop.ps1"')
    master_stop_lines.append("  if (Test-Path $stopScript) {")
    master_stop_lines.append('    Write-Host ("Stopping " + $rel)')
    master_stop_lines.append('    powershell -ExecutionPolicy Bypass -File $stopScript')
    master_stop_lines.append("    continue")
    master_stop_lines.append("  }")
    master_stop_lines.append('  $composeCandidates = @("docker-compose.yml","docker-compose.yaml","compose.yml","compose.yaml")')
    master_stop_lines.append('  $compose = $composeCandidates | ForEach-Object { Join-Path $appRoot $_ } | Where-Object { Test-Path $_ } | Select-Object -First 1')
    master_stop_lines.append("  if ($compose) {")
    master_stop_lines.append('    $project = ("lnc-" + $app.Name).ToLowerInvariant()')
    master_stop_lines.append('    Write-Host ("Stopping docker compose for " + $rel + " (project " + $project + ")")')
    master_stop_lines.append('    docker compose -f $compose -p $project down')
    master_stop_lines.append("    continue")
    master_stop_lines.append("  }")
    master_stop_lines.append('  Write-Host ("No stop script or compose file for " + $rel + ".")')
    master_stop_lines.append("}")
    master_stop_text = "\n".join(master_stop_lines) + "\n"

    # Root helpers
    docker_up_lines: list[str] = []
    docker_up_lines.append('$ErrorActionPreference = "Stop"')
    docker_up_lines.append("")
    docker_up_lines.append("# Auto-generated by Local Nexus Controller")
    docker_up_lines.append("# Starts docker compose for every app under apps/* that has a compose file.")
    docker_up_lines.append("")
    docker_up_lines.append('$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot \"..\\..\" )).Path')
    docker_up_lines.append("Set-Location $repoRoot")
    docker_up_lines.append('$appsRoot = Join-Path $repoRoot "apps"')
    docker_up_lines.append('if (!(Test-Path $appsRoot)) { Write-Host "No apps/ folder found."; exit 0 }')
    docker_up_lines.append('$apps = Get-ChildItem -Path $appsRoot -Directory -ErrorAction SilentlyContinue')
    docker_up_lines.append('  $composeCandidates = @("docker-compose.yml","docker-compose.yaml","compose.yml","compose.yaml")')
    docker_up_lines.append("foreach ($app in $apps) {")
    docker_up_lines.append('  $appRoot = $app.FullName')
    docker_up_lines.append('  $rel = Join-Path "apps" $app.Name')
    docker_up_lines.append('  $compose = $composeCandidates | ForEach-Object { Join-Path $appRoot $_ } | Where-Object { Test-Path $_ } | Select-Object -First 1')
    docker_up_lines.append("  if (!$compose) { continue }")
    docker_up_lines.append('  $project = ("lnc-" + $app.Name).ToLowerInvariant()')
    docker_up_lines.append('  Write-Host ("docker compose up: " + $rel + " (project " + $project + ")")')
    docker_up_lines.append('  docker compose -f $compose -p $project up -d')
    docker_up_lines.append("}")
    docker_up_text = "\n".join(docker_up_lines) + "\n"

    docker_down_lines: list[str] = []
    docker_down_lines.append('$ErrorActionPreference = "Stop"')
    docker_down_lines.append("")
    docker_down_lines.append("# Auto-generated by Local Nexus Controller")
    docker_down_lines.append("# Stops docker compose for every app under apps/* that has a compose file.")
    docker_down_lines.append("")
    docker_down_lines.append('$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot \"..\\..\" )).Path')
    docker_down_lines.append("Set-Location $repoRoot")
    docker_down_lines.append('$appsRoot = Join-Path $repoRoot "apps"')
    docker_down_lines.append('if (!(Test-Path $appsRoot)) { Write-Host "No apps/ folder found."; exit 0 }')
    docker_down_lines.append('$apps = Get-ChildItem -Path $appsRoot -Directory -ErrorAction SilentlyContinue')
    docker_down_lines.append('  $composeCandidates = @("docker-compose.yml","docker-compose.yaml","compose.yml","compose.yaml")')
    docker_down_lines.append("foreach ($app in $apps) {")
    docker_down_lines.append('  $appRoot = $app.FullName')
    docker_down_lines.append('  $rel = Join-Path "apps" $app.Name')
    docker_down_lines.append('  $compose = $composeCandidates | ForEach-Object { Join-Path $appRoot $_ } | Where-Object { Test-Path $_ } | Select-Object -First 1')
    docker_down_lines.append("  if (!$compose) { continue }")
    docker_down_lines.append('  $project = ("lnc-" + $app.Name).ToLowerInvariant()')
    docker_down_lines.append('  Write-Host ("docker compose down: " + $rel + " (project " + $project + ")")')
    docker_down_lines.append('  docker compose -f $compose -p $project down')
    docker_down_lines.append("}")
    docker_down_text = "\n".join(docker_down_lines) + "\n"

    env_lines: list[str] = []
    env_lines.append('$ErrorActionPreference = "Stop"')
    env_lines.append("")
    env_lines.append("# Auto-generated by Local Nexus Controller")
    env_lines.append("# Aggregates .env.example files from root and apps/* into LOCAL_NEXUS.env.example")
    env_lines.append("")
    env_lines.append('$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot \"..\\..\" )).Path')
    env_lines.append("Set-Location $repoRoot")
    env_lines.append('$outPath = Join-Path $repoRoot "LOCAL_NEXUS.env.example"')
    env_lines.append('$sb = New-Object System.Text.StringBuilder')
    env_lines.append('$candidates = New-Object System.Collections.Generic.List[string]')
    env_lines.append('$rootExample = Join-Path $repoRoot ".env.example"')
    env_lines.append('if (Test-Path $rootExample) { [void]$candidates.Add($rootExample) }')
    env_lines.append('$appsRoot = Join-Path $repoRoot "apps"')
    env_lines.append('if (Test-Path $appsRoot) {')
    env_lines.append('  Get-ChildItem -Path $appsRoot -Directory -ErrorAction SilentlyContinue | ForEach-Object {')
    env_lines.append('    $p = Join-Path $_.FullName ".env.example"')
    env_lines.append('    if (Test-Path $p) { [void]$candidates.Add($p) }')
    env_lines.append("  }")
    env_lines.append("}")
    env_lines.append('foreach ($p in $candidates) {')
    env_lines.append('  [void]$sb.AppendLine("### " + $p.Replace($repoRoot + "\\", ""))')
    env_lines.append('  [void]$sb.AppendLine((Get-Content -Raw -Path $p))')
    env_lines.append('  [void]$sb.AppendLine("")')
    env_lines.append("}")
    env_lines.append('Set-Content -Path $outPath -Value $sb.ToString() -Encoding UTF8')
    env_lines.append('Write-Host ("Wrote: " + $outPath)')
    env_text = "\n".join(env_lines) + "\n"

    port_lines: list[str] = []
    port_lines.append('$ErrorActionPreference = "Stop"')
    port_lines.append("")
    port_lines.append("# Auto-generated by Local Nexus Controller")
    port_lines.append("# Simple port visibility helper (Windows).")
    port_lines.append("")
    port_lines.append('Write-Host "Listening ports (TCP) - top 50:"')
    port_lines.append('try {')
    port_lines.append('  Get-NetTCPConnection -State Listen | Select-Object -First 50 LocalAddress,LocalPort,OwningProcess | Format-Table -AutoSize')
    port_lines.append('} catch {')
    port_lines.append('  netstat -ano | Select-String "LISTENING" | Select-Object -First 50')
    port_lines.append('}')
    port_lines.append("")
    port_lines.append('Write-Host "Tip: run the dashboard action Resolve ports to fix reserved port conflicts for registered services."')
    port_text = "\n".join(port_lines) + "\n"

    for rel_path, content_text in [
        (master_start, master_start_text),
        (master_stop, master_stop_text),
        (master_docker_up, docker_up_text),
        (master_docker_down, docker_down_text),
        (master_env_agg, env_text),
        (master_port_check, port_text),
    ]:
        if rel_path in dst_existing_paths:
            warnings.append(f"Skipped generating (already exists): {rel_path}")
            continue
        b64 = base64.b64encode(content_text.encode("utf-8")).decode("utf-8")
        sha = _github_create_blob(dst_owner, dst_repo, b64, token)
        tree_items.append({"path": rel_path, "mode": "100644", "type": "blob", "sha": sha})

    if master_bundle_path not in dst_existing_paths:
        master_bundle = {
            "service": {
                "name": f"{dst_repo}-master",
                "description": f"Master program for {dst_full} (includes {src_full} under {subdir})",
                "category": "apps",
                "tags": ["master", "monorepo", "github"],
                "tech_stack": ["git", "powershell"],
                "dependencies": [],
                "config_paths": [],
                "port": None,
                "local_url": None,
                "healthcheck_url": None,
                "working_directory": "{REPO_ROOT}",
                "start_command": "powershell -ExecutionPolicy Bypass -File tools\\local-nexus\\start-all.ps1",
                "stop_command": "powershell -ExecutionPolicy Bypass -File tools\\local-nexus\\stop-all.ps1",
                "restart_command": "",
                "env_overrides": {},
                "database_id": None,
                "database_connection_string": None,
                "database_schema_overview": None,
            },
            "database": None,
            "keys": [],
            "requested_port": None,
            "auto_assign_port": False,
            "auto_create_db": False,
            "meta": {
                "source": "github-merge",
                "destination": dst_full,
                "merged_repo": src_full,
                "merged_subdir": subdir,
                "notes": "Import this bundle to control the combined 'master program'. Replace {REPO_ROOT} with your local clone path.",
            },
        }
        master_bundle_text = json.dumps(master_bundle, indent=2) + "\n"
        b64 = base64.b64encode(master_bundle_text.encode("utf-8")).decode("utf-8")
        sha = _github_create_blob(dst_owner, dst_repo, b64, token)
        tree_items.append({"path": master_bundle_path, "mode": "100644", "type": "blob", "sha": sha})
    else:
        warnings.append(f"Skipped generating (already exists): {master_bundle_path}")

    # Generate one bundle per app under apps/* (skip if already present).
    # We infer app names from existing destination tree + newly added merge paths.
    app_names: set[str] = set()
    for p in list(dst_existing_paths) + [str(t.get("path") or "") for t in tree_items]:
        if not p.startswith("apps/"):
            continue
        parts = p.split("/")
        if len(parts) >= 2 and parts[1]:
            app_names.add(parts[1])

    # Helper to check if a path is in the new tree.
    new_paths = {str(t.get("path") or "") for t in tree_items if t.get("path")}

    for app in sorted(app_names):
        app_bundle_path = f"apps/{app}/local-nexus.bundle.json"
        if app_bundle_path in dst_existing_paths or app_bundle_path in new_paths:
            continue

        app_start = f"apps/{app}/tools/local-nexus/start.ps1"
        app_stop = f"apps/{app}/tools/local-nexus/stop.ps1"
        has_start = (app_start in dst_existing_paths) or (app_start in new_paths)
        has_stop = (app_stop in dst_existing_paths) or (app_stop in new_paths)

        app_bundle = {
            "service": {
                "name": app,
                "description": f"App {app} inside {dst_full}",
                "category": "apps",
                "tags": ["app", "monorepo"],
                "tech_stack": ["git", "powershell"],
                "dependencies": [],
                "config_paths": [],
                "port": None,
                "local_url": None,
                "healthcheck_url": None,
                "working_directory": f"{{REPO_ROOT}}\\\\apps\\\\{app}",
                "start_command": (
                    f"powershell -ExecutionPolicy Bypass -File apps\\\\{app}\\\\tools\\\\local-nexus\\\\start.ps1"
                    if has_start
                    else ""
                ),
                "stop_command": (
                    f"powershell -ExecutionPolicy Bypass -File apps\\\\{app}\\\\tools\\\\local-nexus\\\\stop.ps1"
                    if has_stop
                    else ""
                ),
                "restart_command": "",
                "env_overrides": {},
                "database_id": None,
                "database_connection_string": None,
                "database_schema_overview": None,
            },
            "database": None,
            "keys": [],
            "requested_port": None,
            "auto_assign_port": False,
            "auto_create_db": False,
            "meta": {
                "source": "github-merge",
                "destination": dst_full,
                "app": app,
                "needs_local_setup": not has_start,
                "notes": "Import this bundle to control a single app. Replace {REPO_ROOT} with your local clone path.",
            },
        }
        app_bundle_text = json.dumps(app_bundle, indent=2) + "\n"
        b64 = base64.b64encode(app_bundle_text.encode("utf-8")).decode("utf-8")
        sha = _github_create_blob(dst_owner, dst_repo, b64, token)
        tree_items.append({"path": app_bundle_path, "mode": "100644", "type": "blob", "sha": sha})

    manifest = {
        "source": src_full,
        "source_ref": src_ref,
        "destination": dst_full,
        "destination_subdir": subdir,
        "files_copied": created_files,
        "total_bytes": total_bytes,
        "notes": "Copied via Local Nexus Controller (no git history).",
    }
    manifest_text = json.dumps(manifest, indent=2) + "\n"
    manifest_b64 = base64.b64encode(manifest_text.encode("utf-8")).decode("utf-8")
    manifest_blob_sha = _github_create_blob(dst_owner, dst_repo, manifest_b64, token)
    tree_items.append({"path": f"{subdir}/LOCAL_NEXUS_MERGE_MANIFEST.json", "mode": "100644", "type": "blob", "sha": manifest_blob_sha})

    new_tree_sha = _github_create_tree(dst_owner, dst_repo, base_tree_sha, tree_items, token)
    commit_sha = _github_create_commit(
        dst_owner,
        dst_repo,
        f"Merge {src_full}@{src_ref} into {subdir}",
        new_tree_sha,
        base_sha,
        token,
    )
    _github_update_ref(dst_owner, dst_repo, branch_name, commit_sha, token)

    pr_body = (
        f"Copies `{src_full}` ({src_ref}) into `{subdir}`.\n\n"
        f"- Files copied: {created_files}\n"
        f"- Total bytes: {total_bytes}\n"
        "- Note: this is a file copy (no git history)."
    )
    pr = _github_api_request(
        "POST",
        f"https://api.github.com/repos/{dst_owner}/{dst_repo}/pulls",
        token,
        body={"title": f"Merge {src_full} into {dst_repo}", "head": branch_name, "base": base_branch, "body": pr_body},
    )
    if not isinstance(pr, dict):
        raise HTTPException(status_code=400, detail="Failed to create PR (unexpected response).")

    return {
        "status": "created",
        "source": src_full,
        "source_ref": src_ref,
        "destination": dst_full,
        "base": base_branch,
        "branch": branch_name,
        "subdir": subdir,
        "files_copied": created_files,
        "total_bytes": total_bytes,
        "warnings": warnings,
        "pr_url": pr.get("html_url"),
    }


@router.post("/github-workspace-prepare", dependencies=[Depends(require_token)])
def github_workspace_prepare(req: GitHubWorkspacePrepareRequest) -> dict:
    token = (req.github_token or "").strip()
    if not token:
        raise HTTPException(status_code=400, detail="GitHub token required. Click 'GitHub token' and paste one.")

    owner, repo, _, _ = _parse_github_input(req.repo, "main", "x")
    branch = (req.branch or "").strip()
    if not branch:
        raise HTTPException(status_code=400, detail="branch is required (e.g. local-nexus/merge-...).")

    workspaces_root = (Path(__file__).resolve().parents[2] / "data" / "workspaces").resolve()
    workspaces_root.mkdir(parents=True, exist_ok=True)
    ws_dir = workspaces_root / _safe_workspace_name(owner, repo, branch)

    repo_url = f"https://github.com/{owner}/{repo}.git"

    if not ws_dir.exists():
        ws_dir.mkdir(parents=True, exist_ok=True)
        # Clone default branch shallow-ish, then fetch the PR branch.
        code, out = _run_git(["clone", repo_url, "."], cwd=ws_dir, token=token, timeout_s=600)
        if code != 0:
            raise HTTPException(status_code=400, detail=f"git clone failed: {out}")
    else:
        code, out = _run_git(["status", "--porcelain"], cwd=ws_dir, token=token)
        if code != 0:
            raise HTTPException(status_code=400, detail=f"Workspace exists but is not a git repo: {out}")

    # Ensure branch exists locally and is up to date.
    _run_git(["fetch", "origin", branch], cwd=ws_dir, token=token, timeout_s=600)
    code, out = _run_git(["checkout", branch], cwd=ws_dir, token=token)
    if code != 0:
        # Create local branch tracking origin/branch
        code2, out2 = _run_git(["checkout", "-b", branch, f"origin/{branch}"], cwd=ws_dir, token=token)
        if code2 != 0:
            raise HTTPException(status_code=400, detail=f"git checkout failed: {out}\n{out2}".strip())

    _run_git(["pull", "--ff-only", "origin", branch], cwd=ws_dir, token=token, timeout_s=600)

    return {
        "status": "ready",
        "repo": f"{owner}/{repo}",
        "branch": branch,
        "workspace_path": str(ws_dir),
        "next": "Use 'Open in Cursor' to edit, then 'Push fixes' to update the PR on GitHub.",
    }


@router.post("/github-workspace-open", dependencies=[Depends(require_token)])
def github_workspace_open(req: GitHubWorkspaceOpenRequest) -> dict:
    ws = Path(req.workspace_path).expanduser().resolve()
    if not ws.exists():
        raise HTTPException(status_code=400, detail=f"Workspace not found: {ws}")

    cursor_cmd = _find_cursor_command()
    if not cursor_cmd:
        raise HTTPException(status_code=400, detail="Cursor not found. Install Cursor or ensure 'cursor' is on PATH.")

    try:
        subprocess.Popen([*cursor_cmd, str(ws)], cwd=str(ws), shell=False)  # noqa: S603
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Failed to open Cursor: {e}")

    return {"status": "opened", "workspace_path": str(ws)}


@router.post("/github-workspace-push", dependencies=[Depends(require_token)])
def github_workspace_push(req: GitHubWorkspacePushRequest) -> dict:
    token = (req.github_token or "").strip()
    if not token:
        raise HTTPException(status_code=400, detail="GitHub token required. Click 'GitHub token' and paste one.")

    ws = Path(req.workspace_path).expanduser().resolve()
    if not ws.exists():
        raise HTTPException(status_code=400, detail=f"Workspace not found: {ws}")
    branch = (req.branch or "").strip()
    if not branch:
        raise HTTPException(status_code=400, detail="branch is required.")

    # Ensure we're on the right branch.
    _run_git(["checkout", branch], cwd=ws, token=token)

    code, out = _run_git(["status", "--porcelain"], cwd=ws, token=token)
    if code != 0:
        raise HTTPException(status_code=400, detail=f"git status failed: {out}")
    if not out.strip():
        return {"status": "noop", "message": "No changes to commit.", "workspace_path": str(ws), "branch": branch}

    _run_git(["add", "-A"], cwd=ws, token=token)
    msg = (req.commit_message or "").strip() or "Fix after merge/localize in Cursor"
    code, out = _run_git(["commit", "-m", msg], cwd=ws, token=token)
    if code != 0 and "nothing to commit" not in out.lower():
        raise HTTPException(status_code=400, detail=f"git commit failed: {out}")

    code, out = _run_git(["push", "origin", f"HEAD:{branch}"], cwd=ws, token=token, timeout_s=600)
    if code != 0:
        raise HTTPException(status_code=400, detail=f"git push failed: {out}")

    return {"status": "pushed", "workspace_path": str(ws), "branch": branch, "message": "Pushed fixes to GitHub PR branch."}


@router.post("/github-list-bundles", dependencies=[Depends(require_token)])
def github_list_bundles(req: GitHubListBundlesRequest) -> dict:
    """
    Lists Local Nexus bundle files in a repo/ref:
    - local-nexus.apps.bundle.json (master)
    - apps/*/local-nexus.bundle.json (per-app)
    - local-nexus.bundle.json (root, optional)
    """

    token = (req.github_token or "").strip()
    if not token:
        raise HTTPException(status_code=400, detail="GitHub token required. Click 'GitHub token' and paste one.")

    owner, repo, ref, _ = _parse_github_input(req.repo, req.ref, "x")
    entries = _github_get_tree_entries(owner, repo, ref, token)
    paths = sorted({str(e.get("path")) for e in entries if e.get("type") == "blob" and e.get("path")})

    bundles: list[dict[str, Any]] = []
    for p in paths:
        if p == "local-nexus.apps.bundle.json":
            bundles.append({"type": "master", "app": None, "path": p})
        elif p == "local-nexus.bundle.json":
            bundles.append({"type": "root", "app": None, "path": p})
        elif p.startswith("apps/") and p.endswith("/local-nexus.bundle.json"):
            parts = p.split("/")
            app = parts[1] if len(parts) >= 3 else None
            bundles.append({"type": "app", "app": app, "path": p})

    return {"repo": f"{owner}/{repo}", "ref": ref, "count": len(bundles), "bundles": bundles}


@router.post("/github-device-start", dependencies=[Depends(require_token)])
def github_device_start(req: GitHubDeviceStartRequest) -> dict:
    payload = _github_device_start(req.scope)
    # Return only the fields the UI needs.
    return {
        "device_code": payload.get("device_code"),
        "user_code": payload.get("user_code"),
        "verification_uri": payload.get("verification_uri"),
        "expires_in": payload.get("expires_in"),
        "interval": payload.get("interval"),
        "scope": req.scope,
    }


@router.post("/github-device-poll", dependencies=[Depends(require_token)])
def github_device_poll(req: GitHubDevicePollRequest) -> dict:
    if not (req.device_code or "").strip():
        raise HTTPException(status_code=400, detail="device_code is required")
    payload = _github_device_poll(req.device_code.strip())

    # Map common device-flow statuses.
    if payload.get("access_token"):
        return {"status": "authorized", "access_token": payload.get("access_token"), "token_type": payload.get("token_type")}

    err = payload.get("error")
    if err in {"authorization_pending", "slow_down", "expired_token", "access_denied"}:
        return {"status": str(err), "error_description": payload.get("error_description")}

    return {"status": "unknown", "raw": payload}

@router.post("/scan-bundles", dependencies=[Depends(require_token)])
def scan_and_import_bundles(req: ScanBundlesRequest, session: Session = Depends(get_session)) -> dict:
    root = Path(req.root).expanduser()
    if not root.exists() or not root.is_dir():
        raise HTTPException(status_code=400, detail=f"Folder not found: {root}")

    bundle_paths: list[Path] = []
    for p in root.rglob(req.bundle_filename):
        if p.is_file():
            bundle_paths.append(p)
        if len(bundle_paths) >= int(req.max_files):
            break

    roots_with_bundle = {p.parent.resolve() for p in bundle_paths}

    repo_roots: list[Path] = []
    if req.include_git_repos:
        for git_dir in root.rglob(".git"):
            if not git_dir.is_dir():
                continue
            repo_root = git_dir.parent.resolve()
            if repo_root in roots_with_bundle:
                continue
            repo_roots.append(repo_root)
            if len(repo_roots) >= int(req.max_repos):
                break

    results: list[dict] = []
    errors: list[dict] = []

    for p in bundle_paths:
        try:
            payload = json.loads(p.read_text(encoding="utf-8"))
            bundle = ImportBundle.model_validate(payload)  # type: ignore[attr-defined]
        except Exception as e:  # noqa: BLE001 - return readable error to UI
            errors.append({"path": str(p), "error": str(e)})
            continue

        if req.dry_run:
            results.append({"type": "bundle", "path": str(p), "service_name": bundle.service.name})
            continue

        try:
            res = import_bundle_impl(session, bundle)
            results.append(
                {
                    "type": "bundle",
                    "path": str(p),
                    "service_name": bundle.service.name,
                    "service_id": res.service_id,
                    "database_id": res.database_id,
                    "warnings": res.warnings,
                }
            )
        except Exception as e:  # noqa: BLE001 - continue importing other bundles
            errors.append({"path": str(p), "service_name": bundle.service.name, "error": str(e)})

    for repo_root in repo_roots:
        repo_name = repo_root.name
        bundle = ImportBundle(
            service=ServiceCreate(
                name=repo_name,
                description=f"Imported from local Git repo at {repo_root}",
                category="repos",
                tags=["github"],
                tech_stack=["git"],
                dependencies=[],
                config_paths=[],
                port=None,
                local_url=None,
                healthcheck_url=None,
                working_directory=str(repo_root),
                start_command="",
                stop_command="",
                restart_command="",
                env_overrides={},
                database_id=None,
                database_connection_string=None,
                database_schema_overview=None,
            ),
            database=None,
            keys=[],
            requested_port=None,
            auto_assign_port=False,
            auto_create_db=False,
            meta={"source": "git-scan", "path": str(repo_root)},
        )

        if req.dry_run:
            results.append({"type": "git-repo", "path": str(repo_root), "service_name": repo_name})
            continue

        try:
            res = import_bundle_impl(session, bundle)
            results.append(
                {
                    "type": "git-repo",
                    "path": str(repo_root),
                    "service_name": repo_name,
                    "service_id": res.service_id,
                    "database_id": res.database_id,
                    "warnings": res.warnings,
                }
            )
        except Exception as e:  # noqa: BLE001 - continue importing other repos
            errors.append({"path": str(repo_root), "service_name": repo_name, "error": str(e)})

    return {
        "root": str(root),
        "bundle_filename": req.bundle_filename,
        "bundles_found": len(bundle_paths),
        "git_repos_found": len(repo_roots),
        "dry_run": bool(req.dry_run),
        "imported": len(results) if not req.dry_run else 0,
        "results": results,
        "errors": errors,
    }


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
