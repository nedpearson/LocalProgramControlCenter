# Auto-start Local Nexus Controller and launch all registered services
# This script:
# 1. Starts the Local Nexus Controller
# 2. Waits for it to be ready
# 3. Triggers auto-start of all services via the API

$ErrorActionPreference = "Stop"

# Function to kill process using a specific port
function Stop-PortProcess {
    param([int]$Port)

    $connections = netstat -ano | Select-String ":$Port\s" | Select-String "LISTENING"

    if ($connections) {
        Write-Host "Found existing process on port $Port. Stopping it..."
        foreach ($connection in $connections) {
            $line = $connection.ToString().Trim()
            $parts = $line -split '\s+' | Where-Object { $_ -ne '' }
            $pid = $parts[-1]

            if ($pid -match '^\d+$') {
                try {
                    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                    Start-Sleep -Milliseconds 500
                    Write-Host "✓ Process stopped (PID: $pid)"
                } catch {
                    # Process already stopped or inaccessible
                }
            }
        }
    }
}

# Get the project root directory
$ProjectRoot = Split-Path -Parent $PSScriptRoot

# Check if virtual environment exists
$VenvPath = Join-Path $ProjectRoot ".venv"
if (-not (Test-Path $VenvPath)) {
    Write-Host "Virtual environment not found. Creating..."
    python -m venv $VenvPath
    & "$VenvPath\Scripts\Activate.ps1"
    pip install -r (Join-Path $ProjectRoot "requirements.txt")
}

# Read port from .env file
$EnvFile = Join-Path $ProjectRoot ".env"
$Port = 5010  # Default port

if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match "^LOCAL_NEXUS_PORT=(.+)$") {
            $Port = $Matches[1]
        }
    }
}

# Stop any existing process on the target port
Stop-PortProcess -Port $Port

# Start the controller in a new hidden window
Write-Host "Starting Local Nexus Controller on port $Port..."
$ProcessInfo = New-Object System.Diagnostics.ProcessStartInfo
$ProcessInfo.FileName = "$VenvPath\Scripts\python.exe"
$ProcessInfo.Arguments = "-m uvicorn local_nexus_controller.main:app --host 0.0.0.0 --port $Port"
$ProcessInfo.WorkingDirectory = $ProjectRoot
$ProcessInfo.UseShellExecute = $false
$ProcessInfo.CreateNoWindow = $true
$Process = [System.Diagnostics.Process]::Start($ProcessInfo)

Write-Host "Controller started (PID: $($Process.Id))"
Write-Host "Waiting for controller to be ready..."

# Wait for the controller to be ready
$MaxAttempts = 30
$Attempt = 0
$Ready = $false

while ($Attempt -lt $MaxAttempts -and -not $Ready) {
    Start-Sleep -Seconds 1
    try {
        $Response = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($Response.StatusCode -eq 200) {
            $Ready = $true
        }
    } catch {
        # Ignore errors, keep trying
    }
    $Attempt++
}

if ($Ready) {
    Write-Host "Controller is ready!"
    Write-Host "Dashboard: http://127.0.0.1:$Port"
    Write-Host ""
    Write-Host "Note: Auto-start is configured in .env (LOCAL_NEXUS_AUTO_START_ALL_ON_BOOT=true)"
    Write-Host "All services with start commands will be launched automatically."
} else {
    Write-Host "Warning: Controller did not respond within timeout."
}
