from __future__ import annotations

import json
import sys
from pathlib import Path

from sqlmodel import Session

from local_nexus_controller.db import engine, init_db
from local_nexus_controller.models import ImportBundle
from local_nexus_controller.services.registry_import import import_bundle


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python tools/import_bundle.py <path-to-bundle.json>")
        print("The JSON may be a single bundle object or a list of bundle objects.")
        return 2

    path = Path(sys.argv[1]).resolve()
    if not path.exists():
        print(f"Bundle not found: {path}")
        return 2

    init_db()
    payload = json.loads(path.read_text(encoding="utf-8"))

    with Session(engine) as session:
        results = []
        if isinstance(payload, list):
            for item in payload:
                bundle = ImportBundle.model_validate(item)  # type: ignore[attr-defined]
                res = import_bundle(session, bundle)
                results.append({"service_id": res.service_id, "database_id": res.database_id, "warnings": res.warnings})
        else:
            bundle = ImportBundle.model_validate(payload)  # type: ignore[attr-defined]
            res = import_bundle(session, bundle)
            results.append({"service_id": res.service_id, "database_id": res.database_id, "warnings": res.warnings})

    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
