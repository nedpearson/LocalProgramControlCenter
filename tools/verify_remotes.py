from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RepoSpec:
    path: str
    name: str
    expected_origin: str
    expected_branch: str = "main"


def _run_git(repo_path: Path, args: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(
        ["git", "-C", str(repo_path), *args],
        capture_output=True,
        text=True,
    )
    return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()


def _load_specs(config_path: Path) -> list[RepoSpec]:
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    repos = raw.get("repos")
    if not isinstance(repos, list):
        raise SystemExit("Config must contain a top-level 'repos' list.")

    out: list[RepoSpec] = []
    for i, item in enumerate(repos, start=1):
        if not isinstance(item, dict):
            raise SystemExit(f"repos[{i}] must be an object.")
        path = str(item.get("path") or "").strip()
        name = str(item.get("name") or "").strip()
        expected_origin = str(item.get("expected_origin") or "").strip()
        expected_branch = str(item.get("expected_branch") or "main").strip()
        if not path or not expected_origin:
            raise SystemExit(f"repos[{i}] must include 'path' and 'expected_origin'.")
        out.append(
            RepoSpec(
                path=path,
                name=name or Path(path).name,
                expected_origin=expected_origin,
                expected_branch=expected_branch or "main",
            )
        )
    return out


def _is_git_repo(repo_path: Path) -> bool:
    rc, out, _ = _run_git(repo_path, ["rev-parse", "--is-inside-work-tree"])
    return rc == 0 and out.lower() == "true"


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify each repo points to the correct origin URL.")
    ap.add_argument(
        "--config",
        default=str(Path(__file__).resolve().parents[1] / "repo_remotes.json"),
        help="Path to repo_remotes.json (defaults to controller repo root).",
    )
    ap.add_argument("--fix", action="store_true", help="Apply fixes (set origin URL and rename branch).")
    args = ap.parse_args()

    config_path = Path(args.config).expanduser().resolve()
    if not config_path.exists():
        print(f"Config not found: {config_path}", file=sys.stderr)
        return 2

    specs = _load_specs(config_path)
    failures: list[str] = []

    for spec in specs:
        repo_path = Path(spec.path).expanduser().resolve()
        label = f"{spec.name} ({repo_path})"

        if not repo_path.exists():
            failures.append(f"{label}: path does not exist")
            continue

        if not _is_git_repo(repo_path):
            failures.append(f"{label}: not a git repo")
            continue

        rc, origin, err = _run_git(repo_path, ["remote", "get-url", "origin"])
        if rc != 0:
            failures.append(f"{label}: missing origin remote ({err or 'unknown error'})")
            continue

        if origin != spec.expected_origin:
            msg = f"{label}: origin mismatch\n  actual:   {origin}\n  expected: {spec.expected_origin}"
            if args.fix:
                rc2, _, err2 = _run_git(repo_path, ["remote", "set-url", "origin", spec.expected_origin])
                if rc2 != 0:
                    failures.append(msg + f"\n  fix_failed: {err2 or 'unknown error'}")
                else:
                    print(msg + "\n  fixed: set-url origin")
            else:
                failures.append(msg)

        # Branch check (best effort)
        rc, branch, _ = _run_git(repo_path, ["branch", "--show-current"])
        if rc == 0 and branch and branch != spec.expected_branch:
            msg = f"{label}: branch mismatch\n  actual:   {branch}\n  expected: {spec.expected_branch}"
            if args.fix:
                rc2, _, err2 = _run_git(repo_path, ["branch", "-M", spec.expected_branch])
                if rc2 != 0:
                    failures.append(msg + f"\n  fix_failed: {err2 or 'unknown error'}")
                else:
                    print(msg + "\n  fixed: branch -M")
            else:
                failures.append(msg)

    if failures:
        print("\nVERIFY FAILED:")
        for f in failures:
            print(f"- {f}")
        return 1

    print("OK: all repos match expected origin/branch.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

