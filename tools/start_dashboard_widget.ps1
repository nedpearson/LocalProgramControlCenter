$ErrorActionPreference = "Stop"

# Starts the Local Nexus Controller server and opens a small dashboard window
# in the bottom-left corner of the primary monitor.
#
# Intended to be used at user logon (Startup shortcut / HKCU Run).

function Write-WidgetLog([string]$projectRoot, [string]$message) {
  try {
    $logDir = Join-Path $projectRoot "data\logs"
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    $logPath = Join-Path $logDir "dashboard-widget.log"
    $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss.fff")
    Add-Content -Path $logPath -Value "[$ts] $message"
  } catch {
    # Best-effort logging only.
  }
}

function Enter-WidgetLock {
  if ($env:LOCAL_NEXUS_WIDGET_FORCE -eq "1") { return $true }

  $lockDir = Join-Path $env:LocalAppData "LocalNexusController"
  New-Item -ItemType Directory -Force -Path $lockDir | Out-Null
  $lockPath = Join-Path $lockDir "dashboard-widget.lock"

  # If we ran very recently (e.g., both Startup shortcut and HKCU Run), exit.
  if (Test-Path $lockPath) {
    $age = (Get-Date) - (Get-Item $lockPath).LastWriteTime
    if ($age.TotalSeconds -lt 45) { return $false }
  }

  Set-Content -Path $lockPath -Value (Get-Date).ToString("o")
  return $true
}

function Resolve-ProjectRoot {
  $here = Split-Path -Parent $PSCommandPath
  return (Resolve-Path (Join-Path $here "..")).Path
}

function Get-PythonExe([string]$projectRoot) {
  $venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
  if (Test-Path $venvPython) { return $venvPython }
  $py = (Get-Command py -ErrorAction SilentlyContinue)
  if ($py) { return $py.Source }
  $python = (Get-Command python -ErrorAction SilentlyContinue)
  if ($python) { return $python.Source }
  throw "Python not found. Run .\run.ps1 once to create the venv."
}

function Get-BrowserCmd {
  foreach ($name in @("msedge", "chrome", "brave")) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
  }

  $candidates = @(
    (Join-Path $env:ProgramFiles "Microsoft\Edge\Application\msedge.exe"),
    (Join-Path ${env:ProgramFiles(x86)} "Microsoft\Edge\Application\msedge.exe"),
    (Join-Path $env:LocalAppData "Microsoft\Edge\Application\msedge.exe"),
    (Join-Path $env:ProgramFiles "Google\Chrome\Application\chrome.exe"),
    (Join-Path ${env:ProgramFiles(x86)} "Google\Chrome\Application\chrome.exe"),
    (Join-Path $env:LocalAppData "Google\Chrome\Application\chrome.exe"),
    (Join-Path $env:ProgramFiles "BraveSoftware\Brave-Browser\Application\brave.exe"),
    (Join-Path ${env:ProgramFiles(x86)} "BraveSoftware\Brave-Browser\Application\brave.exe"),
    (Join-Path $env:LocalAppData "BraveSoftware\Brave-Browser\Application\brave.exe")
  )

  foreach ($p in $candidates) {
    if ($p -and (Test-Path $p)) { return $p }
  }

  throw "No supported browser found (Edge/Chrome/Brave). Install one, or add it to PATH."
}

function Get-WorkingArea {
  Add-Type -AssemblyName System.Windows.Forms | Out-Null
  return [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea
}

function Start-Server([string]$pythonExe, [string]$projectRoot) {
  $logDir = Join-Path $projectRoot "data\logs"
  New-Item -ItemType Directory -Force -Path $logDir | Out-Null
  $outLogPath = Join-Path $logDir "local-nexus-startup.stdout.log"
  $errLogPath = Join-Path $logDir "local-nexus-startup.stderr.log"

  # We open the dashboard window ourselves (in a specific size/position), so disable
  # the built-in "open default browser tab" behavior for this process.
  $env:LOCAL_NEXUS_OPEN_BROWSER = "false"

  Start-Process `
    -FilePath $pythonExe `
    -ArgumentList @("-m", "local_nexus_controller") `
    -WorkingDirectory $projectRoot `
    -WindowStyle Hidden `
    -RedirectStandardOutput $outLogPath `
    -RedirectStandardError $errLogPath | Out-Null
}

function Wait-For-Dashboard([string]$url, [int]$timeoutSeconds = 25) {
  $deadline = (Get-Date).AddSeconds($timeoutSeconds)
  while ((Get-Date) -lt $deadline) {
    try {
      $res = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 2
      if ($res.StatusCode -ge 200 -and $res.StatusCode -lt 500) { return }
    } catch {
      Start-Sleep -Milliseconds 500
    }
  }
}

function Test-DashboardUp([string]$url) {
  try {
    $res = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 1
    return ($res.StatusCode -ge 200 -and $res.StatusCode -lt 500)
  } catch {
    return $false
  }
}

function Open-WidgetWindow([string]$browserExe, [string]$url) {
  $wa = Get-WorkingArea

  # Tweak these to taste.
  # Smaller footprint, but a bit wider for readability.
  $w = $widgetWidth
  $h = $widgetHeight
  $margin = $widgetMargin
  $x = $margin
  $y = [Math]::Max(0, $wa.Bottom - $h - $margin)

  $browserArgs = @(
    "--app=$url",
    "--window-size=$w,$h",
    "--window-position=$x,$y"
  )

  Start-Process -FilePath $browserExe -ArgumentList $browserArgs | Out-Null
}

function ConvertTo-Bool([string]$value, [bool]$default) {
  if ($null -eq $value -or $value.Trim() -eq "") { return $default }
  $v = $value.Trim().ToLowerInvariant()
  return @("1", "true", "yes", "on").Contains($v)
}

function ConvertTo-Int([string]$value, [int]$default) {
  try {
    if ($null -eq $value -or $value.Trim() -eq "") { return $default }
    return [int]$value.Trim()
  } catch {
    return $default
  }
}

function Test-InternetUp {
  try {
    # DNS resolution check (fast).
    [void][System.Net.Dns]::GetHostEntry("example.com")

    # HTTP connectivity check (short timeout).
    $res = Invoke-WebRequest -UseBasicParsing -Uri "http://www.msftconnecttest.com/connecttest.txt" -TimeoutSec 3
    return ($res.StatusCode -ge 200 -and $res.StatusCode -lt 400)
  } catch {
    return $false
  }
}

function Wait-For-Internet([int]$timeoutSeconds) {
  $deadline = (Get-Date).AddSeconds($timeoutSeconds)
  $lastLog = Get-Date "2000-01-01"

  while ((Get-Date) -lt $deadline) {
    if (Test-InternetUp) { return $true }

    $now = Get-Date
    if (($now - $lastLog).TotalSeconds -ge 10) {
      Write-WidgetLog $projectRoot "Waiting for internet connectivity..."
      $lastLog = $now
    }
    Start-Sleep -Seconds 2
  }
  return $false
}

$projectRoot = Resolve-ProjectRoot
$pythonExe = Get-PythonExe $projectRoot

$port = 5010
$waitForInternet = $true
$internetTimeoutSeconds = 90
$startupDelaySeconds = 12
$widgetWidth = 780
$widgetHeight = 240
$widgetMargin = 8

$envPath = Join-Path $projectRoot ".env"
if (Test-Path $envPath) {
  foreach ($line in (Get-Content $envPath)) {
    if ($line -match '^\s*LOCAL_NEXUS_PORT\s*=\s*(\d+)\s*$') { $port = [int]$Matches[1] }
    if ($line -match '^\s*LOCAL_NEXUS_WAIT_FOR_INTERNET\s*=\s*(.+?)\s*$') { $waitForInternet = ConvertTo-Bool $Matches[1] $waitForInternet }
    if ($line -match '^\s*LOCAL_NEXUS_INTERNET_TIMEOUT_SECONDS\s*=\s*(.+?)\s*$') { $internetTimeoutSeconds = ConvertTo-Int $Matches[1] $internetTimeoutSeconds }
    if ($line -match '^\s*LOCAL_NEXUS_WIDGET_START_DELAY_SECONDS\s*=\s*(.+?)\s*$') { $startupDelaySeconds = ConvertTo-Int $Matches[1] $startupDelaySeconds }
    if ($line -match '^\s*LOCAL_NEXUS_WIDGET_WIDTH\s*=\s*(.+?)\s*$') { $widgetWidth = ConvertTo-Int $Matches[1] $widgetWidth }
    if ($line -match '^\s*LOCAL_NEXUS_WIDGET_HEIGHT\s*=\s*(.+?)\s*$') { $widgetHeight = ConvertTo-Int $Matches[1] $widgetHeight }
    if ($line -match '^\s*LOCAL_NEXUS_WIDGET_MARGIN\s*=\s*(.+?)\s*$') { $widgetMargin = ConvertTo-Int $Matches[1] $widgetMargin }
  }
}

# Give Explorer/network stack a moment to finish loading so the app window is visible,
# and Wi-Fi/Ethernet has time to connect.
Start-Sleep -Seconds $startupDelaySeconds

if (!(Enter-WidgetLock)) {
  Write-WidgetLog $projectRoot "Lock indicates recent run; exiting."
  exit 0
}

# Dashboard URL: prefer loopback for local desktop widget.
$lncHost = "127.0.0.1"
$url = "http://$lncHost`:$port/?widget=1"

Write-WidgetLog $projectRoot "Starting widget. pythonExe=$pythonExe url=$url"

try {
  if (!(Test-DashboardUp $url)) {
    Write-WidgetLog $projectRoot "Dashboard not up; starting server."
    Start-Server $pythonExe $projectRoot
    Wait-For-Dashboard $url 25
  } else {
    Write-WidgetLog $projectRoot "Dashboard already up; not starting server."
  }

  if ($waitForInternet) {
    Write-WidgetLog $projectRoot "Internet wait enabled (timeout=${internetTimeoutSeconds}s)."
    $ok = Wait-For-Internet $internetTimeoutSeconds
    if ($ok) {
      Write-WidgetLog $projectRoot "Internet connectivity detected."
    } else {
      Write-WidgetLog $projectRoot "WARNING: Internet not detected within timeout; opening widget anyway."
    }
  }

  $browserExe = Get-BrowserCmd
  Write-WidgetLog $projectRoot "Using browser: $browserExe"
  Open-WidgetWindow $browserExe $url
  Write-WidgetLog $projectRoot "Widget window opened."
} catch {
  Write-WidgetLog $projectRoot "ERROR: $($_.Exception.Message)"
  throw
}

