from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# Ensure the repo root is importable even when running a script from /tools.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from local_nexus_controller.models import ImportBundle


_HAS_PLACEHOLDER_RE = re.compile(r"(\{[A-Z_]+\}|\$\{[A-Z_]+\}|%[A-Z_]+%)")


def _looks_like_windows_abs_path(p: str) -> bool:
    # Accept both C:\foo and C:/foo
    return bool(re.match(r"^[a-zA-Z]:[\\/]", p))


def _to_posixish(p: str) -> str:
    return p.replace("\\", "/")


def normalize_path_value(value: str) -> str:
    """
    Normalize Windows path strings to use forward slashes.
    If the value looks like an absolute path and does not contain placeholders,
    resolve it to an absolute normalized path.
    """

    v = str(value)
    v = _to_posixish(v)

    if _HAS_PLACEHOLDER_RE.search(v):
        return v

    if _looks_like_windows_abs_path(v):
        try:
            resolved = Path(v).resolve()
            return _to_posixish(str(resolved))
        except Exception:
            # Best-effort: keep the slash-normalized value
            return v

    return v


def normalize_bundle_dict(obj: dict[str, Any]) -> dict[str, Any]:
    out = json.loads(json.dumps(obj))  # deep copy (keeps only JSON types)
    svc = out.get("service") or {}

    if isinstance(svc, dict):
        wd = svc.get("working_directory")
        if isinstance(wd, str) and wd.strip():
            svc["working_directory"] = normalize_path_value(wd)

        cps = svc.get("config_paths")
        if isinstance(cps, list):
            svc["config_paths"] = [normalize_path_value(x) if isinstance(x, str) else x for x in cps]

    out["service"] = svc
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate (and optionally normalize) a Local Nexus Import Bundle JSON.")
    ap.add_argument("path", help="Path to a bundle JSON file (single object or list).")
    ap.add_argument("--normalize", action="store_true", help="Normalize path separators and resolve absolute paths.")
    ap.add_argument(
        "--output",
        help="Write normalized JSON to this path (requires --normalize). If omitted, prints normalized JSON to stdout.",
    )
    args = ap.parse_args()

    path = Path(args.path).expanduser().resolve()
    if not path.exists():
        raise SystemExit(f"Bundle not found: {path}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    items: list[dict[str, Any]]
    if isinstance(payload, list):
        items = payload
    else:
        items = [payload]

    normalized_items: list[dict[str, Any]] = []
    for idx, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise SystemExit(f"Item {idx} is not a JSON object.")
        raw = normalize_bundle_dict(item) if args.normalize else item

        # Validate against the controller schema (raises on error)
        ImportBundle.model_validate(raw)  # type: ignore[attr-defined]
        normalized_items.append(raw)

    print(f"OK: validated {len(normalized_items)} bundle(s) from {path}")

    if args.normalize:
        output_payload: Any = normalized_items if isinstance(payload, list) else normalized_items[0]
        text = json.dumps(output_payload, indent=2, ensure_ascii=False)
        if args.output:
            out_path = Path(args.output).expanduser().resolve()
            out_path.write_text(text + "\n", encoding="utf-8")
            print(f"Wrote normalized bundle to: {out_path}")
        else:
            print(text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

