$ErrorActionPreference = "Stop"

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

if (!(Test-Path ".\.venv")) {
  py -m venv .venv
}

.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

if (!(Test-Path ".\.env")) {
  Copy-Item ".\.env.example" ".\.env"
}

.\.venv\Scripts\python.exe -m local_nexus_controller
