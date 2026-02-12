# Auto-start Local Nexus Controller on Windows startup
# This script starts the controller in the background

$ErrorActionPreference = "Stop"

# Get the project root directory
$ProjectRoot = Split-Path -Parent $PSScriptRoot

# Check if virtual environment exists
$VenvPath = Join-Path $ProjectRoot ".venv"
if (-not (Test-Path $VenvPath)) {
    Write-Host "Virtual environment not found. Creating..."
    python -m venv $VenvPath
    & "$VenvPath\Scripts\Activate.ps1"
    pip install -r (Join-Path $ProjectRoot "requirements.txt")
} else {
    & "$VenvPath\Scripts\Activate.ps1"
}

# Start the controller
Write-Host "Starting Local Nexus Controller..."
python -m local_nexus_controller
