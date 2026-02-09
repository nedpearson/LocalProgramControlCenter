# Local Nexus Controller

Local Nexus Controller is a **Windows-friendly local dashboard + API** to **register, document, monitor, and control** all locally-hosted programs/services you build.

It provides:
- **Service registry** (SQLite)
- **Database registry** (SQLite)
- **Port management** (assignment + conflict detection)
- **Secrets/keys references** (env-var references only; never store real secrets)
- **Process control** (start/stop/restart; logs captured to `data/logs/`)
- **Web dashboard** with drill-downs and an **Import Bundle** feature for auto-populating new programs

## Quick start (PowerShell)

From `C:\Users\nedpe\LocalNexusController`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python -m local_nexus_controller
```

Then open:
- Dashboard: `http://127.0.0.1:5010`
- API docs (Swagger): `http://127.0.0.1:5010/docs`

## Import sample registry (4 services + 2 databases)

```powershell
python .\tools\import_bundle.py .\sample_data\import_bundle.json
```

Or use the dashboard:
- Go to **Import** and paste the JSON bundle.

## Import your existing local programs (auto-generated)

This repo includes a bundle based on what was found on your machine:

```powershell
python .\tools\import_bundle.py .\sample_data\import_existing_bundle.json
```

Or use the dashboard:
- Go to **Import** and paste `sample_data/import_existing_bundle.json`.

## Auto-populating new programs you ask me to generate

When you ask for a new program, you (and I) will produce an **Import Bundle JSON** that you can paste into:
- Dashboard → **Import**, or
- `POST /api/import/bundle`

This ensures every new local program is automatically registered, categorized, assigned a port, and optionally assigned a database.

## Isolation model (recommended)

To keep your controller clean and prevent accidental coupling between programs:

- **Each program lives in its own folder**
- **Each folder is its own Cursor project**
- **Each folder is its own Git repo**
- The controller **never imports program code**. It only references programs by metadata:
  - `working_directory`
  - `start_command` / `stop_command` / `restart_command`
  - ports + URLs + healthcheck URL
  - key *references* (env var names only)

### Per-program registration artifact

Each program repo should include a small, versioned bundle file (recommended name: `local-nexus.bundle.json`) that matches the controller’s `ImportBundle` JSON shape.

You can import it with:

```powershell
python .\tools\import_bundle.py C:\path\to\program\local-nexus.bundle.json
```

Or paste the JSON into Dashboard → **Import**.

You can validate a bundle (and optionally normalize Windows paths) with:

```powershell
python .\tools\validate_bundle.py C:\path\to\program\local-nexus.bundle.json
```

## Notes

- The controller stores **only references** to secrets (e.g., `OPENAI_API_KEY`) and where they are used. It never stores secret values.
- Process control uses stored `start_command`/`stop_command` or the controller can terminate the tracked PID tree.
