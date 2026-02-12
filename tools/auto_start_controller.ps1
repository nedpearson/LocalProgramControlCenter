# Auto-start Local Nexus Controller on Windows startup
# This script starts the controller in the background

$ErrorActionPreference = "Stop"

# Function to kill process using port 5010
function Stop-PortProcess {
    param([int]$Port = 5010)

    $connections = netstat -ano | Select-String ":$Port\s" | Select-String "LISTENING"

    if ($connections) {
        foreach ($connection in $connections) {
            $line = $connection.ToString().Trim()
            $parts = $line -split '\s+' | Where-Object { $_ -ne '' }
            $pid = $parts[-1]

            if ($pid -match '^\d+$') {
                try {
                    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                    Start-Sleep -Milliseconds 500
                } catch {
                    # Process already stopped or inaccessible
                }
            }
        }
    }
}

# Get the project root directory
$ProjectRoot = Split-Path -Parent $PSScriptRoot

# Stop any existing process on port 5010
Stop-PortProcess -Port 5010

# Change to project directory
Set-Location $ProjectRoot

# Check if virtual environment exists
$VenvPath = Join-Path $ProjectRoot ".venv"
if (-not (Test-Path $VenvPath)) {
    python -m venv $VenvPath
    & "$VenvPath\Scripts\Activate.ps1"
    pip install -r (Join-Path $ProjectRoot "requirements.txt")
} else {
    & "$VenvPath\Scripts\Activate.ps1"
}

# Ensure .env file exists
$EnvFile = Join-Path $ProjectRoot ".env"
$EnvExample = Join-Path $ProjectRoot ".env.example"
if (-not (Test-Path $EnvFile) -and (Test-Path $EnvExample)) {
    Copy-Item $EnvExample $EnvFile
}

# Start the controller
python -m local_nexus_controller
