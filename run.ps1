$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Local Nexus Controller - Startup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Function to kill process using port 5010
function Stop-PortProcess {
    param([int]$Port = 5010)

    Write-Host "Checking for processes using port $Port..." -ForegroundColor Yellow

    $connections = netstat -ano | Select-String ":$Port\s" | Select-String "LISTENING"

    if ($connections) {
        foreach ($connection in $connections) {
            $line = $connection.ToString().Trim()
            $parts = $line -split '\s+' | Where-Object { $_ -ne '' }
            $pid = $parts[-1]

            if ($pid -match '^\d+$') {
                try {
                    $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
                    if ($process) {
                        Write-Host "Stopping process $($process.Name) (PID: $pid) using port $Port..." -ForegroundColor Yellow
                        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
                        Start-Sleep -Milliseconds 500
                        Write-Host "✓ Process stopped" -ForegroundColor Green
                    }
                } catch {
                    # Process already stopped or inaccessible
                }
            }
        }
    } else {
        Write-Host "✓ Port $Port is available" -ForegroundColor Green
    }
}

# Stop any existing process on port 5010
Stop-PortProcess -Port 5010

Write-Host ""

if (!(Test-Path ".\.venv")) {
  Write-Host "Creating virtual environment..." -ForegroundColor Yellow
  py -m venv .venv
  Write-Host "✓ Virtual environment created" -ForegroundColor Green
  Write-Host ""
}

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\.venv\Scripts\Activate.ps1

Write-Host "Installing/updating dependencies..." -ForegroundColor Yellow
.\.venv\Scripts\python.exe -m pip install -q -r requirements.txt
Write-Host "✓ Dependencies ready" -ForegroundColor Green
Write-Host ""

if (!(Test-Path ".\.env")) {
  Write-Host "Creating .env file from template..." -ForegroundColor Yellow
  Copy-Item ".\.env.example" ".\.env"
  Write-Host "✓ .env file created" -ForegroundColor Green
  Write-Host ""
}

Write-Host "Starting Local Nexus Controller..." -ForegroundColor Green
Write-Host "Dashboard will be available at: http://127.0.0.1:5010" -ForegroundColor Cyan
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

.\.venv\Scripts\python.exe -m local_nexus_controller
