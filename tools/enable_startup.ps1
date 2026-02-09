$ErrorActionPreference = "Stop"

# Enables dashboard visibility after reboot/logon by creating a shortcut in the
# current user's Startup folder (no admin rights required).
# The shortcut runs the widget launcher which:
# - starts the server
# - opens a small dashboard window bottom-left

$projectRoot = (Resolve-Path (Join-Path (Split-Path -Parent $PSCommandPath) "..")).Path
$scriptPath = Join-Path $projectRoot "tools\start_dashboard_widget.ps1"

if (!(Test-Path $scriptPath)) {
  throw "Missing script: $scriptPath"
}

$startupDir = [Environment]::GetFolderPath("Startup")
$lnkPath = Join-Path $startupDir "Local Nexus Controller Dashboard.lnk"

$wsh = New-Object -ComObject WScript.Shell
$lnk = $wsh.CreateShortcut($lnkPath)
$lnk.TargetPath = "powershell.exe"
$lnk.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""
$lnk.WorkingDirectory = $projectRoot

# 7 = Minimized. Prevents an intrusive PowerShell window on logon.
$lnk.WindowStyle = 7
$lnk.Description = "Start Local Nexus Controller and show dashboard widget"
$lnk.Save()

# Also register via HKCU\...\Run (some systems don't reliably run Startup folder items).
$runKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
$runName = "LocalNexusControllerDashboard"
$runValue = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""
New-Item -Path $runKey -Force | Out-Null
Set-ItemProperty -Path $runKey -Name $runName -Value $runValue

Write-Host "Enabled startup shortcut:"
Write-Host "  $lnkPath"
Write-Host "Enabled HKCU Run entry:"
Write-Host "  $runKey -> $runName"
Write-Host "It will run at next logon/reboot."

