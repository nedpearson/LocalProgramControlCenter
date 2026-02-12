# Disable Windows startup task for Local Nexus Controller

$ErrorActionPreference = "Stop"

$TaskName = "LocalNexusController_AutoStart"

# Check if task exists
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($ExistingTask) {
    Write-Host "Removing scheduled task '$TaskName'..."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "SUCCESS! Auto-start has been disabled."
} else {
    Write-Host "Task '$TaskName' not found. Auto-start is not currently enabled."
}
