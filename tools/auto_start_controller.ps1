# Auto-start Local Nexus Controller on Windows startup
# This script starts the controller robustly with automatic port conflict resolution

$ErrorActionPreference = "Continue"

# Get the absolute project root path
$ScriptPath = $MyInvocation.MyCommand.Path
$ToolsDir = Split-Path -Parent $ScriptPath
$ProjectRoot = Split-Path -Parent $ToolsDir

# Create log directory
$LogDir = Join-Path $ProjectRoot "data\logs"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

$LogFile = Join-Path $LogDir "auto-start.log"

function Write-Log {
    param([string]$Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] $Message"
    Add-Content -Path $LogFile -Value $LogMessage
    Write-Host $LogMessage
}

Write-Log "=== Auto-Start Controller ==="
Write-Log "Project Root: $ProjectRoot"

# Read port from .env
$Port = 5010
$EnvFile = Join-Path $ProjectRoot ".env"
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match "^LOCAL_NEXUS_PORT=(\d+)") {
            $Port = [int]$Matches[1]
            Write-Log "Using port from .env: $Port"
        }
    }
}

# Stop any process using the port
Write-Log "Checking port $Port..."
$connections = netstat -ano | Select-String ":$Port\s" | Select-String "LISTENING"

if ($connections) {
    Write-Log "Found existing process on port $Port. Stopping it..."
    foreach ($connection in $connections) {
        $line = $connection.ToString().Trim()
        $parts = $line -split '\s+' | Where-Object { $_ -ne '' }
        $pid = $parts[-1]

        if ($pid -match '^\d+$') {
            try {
                Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                Start-Sleep -Milliseconds 500
                Write-Log "Stopped process PID: $pid"
            } catch {
                Write-Log "Process $pid already stopped"
            }
        }
    }
}

# Change to project directory
Set-Location $ProjectRoot
Write-Log "Changed to directory: $ProjectRoot"

# Find Python executable
$PythonExe = $null
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (Test-Path $VenvPython) {
    $PythonExe = $VenvPython
    Write-Log "Using venv Python: $VenvPython"
} else {
    # Try to find system Python
    try {
        $PythonCmd = Get-Command python -ErrorAction SilentlyContinue
        if ($PythonCmd) {
            $PythonExe = $PythonCmd.Source
            Write-Log "Using system Python: $PythonExe"
        }
    } catch {
        Write-Log "ERROR: Python not found"
        exit 1
    }
}

if (-not $PythonExe) {
    Write-Log "ERROR: No Python executable found"
    exit 1
}

# Start the controller
Write-Log "Starting Local Nexus Controller..."
try {
    & $PythonExe -m local_nexus_controller
} catch {
    Write-Log "ERROR: Failed to start controller: $_"
    exit 1
}
