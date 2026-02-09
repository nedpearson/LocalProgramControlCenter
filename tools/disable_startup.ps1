$ErrorActionPreference = "Stop"

$startupDir = [Environment]::GetFolderPath("Startup")
$lnkPath = Join-Path $startupDir "Local Nexus Controller Dashboard.lnk"
$taskName = "Local Nexus Controller (Dashboard Widget)"

if (Test-Path $lnkPath) {
  Remove-Item -Force $lnkPath
  Write-Host "Disabled startup shortcut:"
  Write-Host "  $lnkPath"
} else {
  Write-Host "Startup shortcut not found:"
  Write-Host "  $lnkPath"
}

try {
  $runKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
  $runName = "LocalNexusControllerDashboard"
  if (Get-ItemProperty -Path $runKey -Name $runName -ErrorAction SilentlyContinue) {
    Remove-ItemProperty -Path $runKey -Name $runName -ErrorAction SilentlyContinue
    Write-Host "Disabled HKCU Run entry:"
    Write-Host "  $runKey -> $runName"
  }
} catch {
  # Best-effort cleanup; ignore permission issues.
}

try {
  if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "Also removed legacy Scheduled Task:"
    Write-Host "  $taskName"
  }
} catch {
  # Best-effort cleanup; ignore permission issues.
}

