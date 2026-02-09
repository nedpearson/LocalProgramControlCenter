$ErrorActionPreference = "Stop"

if (!(Test-Path ".\.venv")) {
  py -m venv .venv
}

.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

if (!(Test-Path ".\.env")) {
  Copy-Item ".\.env.example" ".\.env"
}

.\.venv\Scripts\python.exe -m local_nexus_controller
