# Setup Windows startup task to launch Local Nexus Controller on boot
# This creates a scheduled task that runs when you log in

$ErrorActionPreference = "Stop"

# Get the project root directory
$ProjectRoot = Split-Path -Parent $PSScriptRoot

# Path to the auto-start script
$AutoStartScript = Join-Path $PSScriptRoot "auto_start_and_launch_all.ps1"

# Task name
$TaskName = "LocalNexusController_AutoStart"

# Check if task already exists
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($ExistingTask) {
    Write-Host "Task '$TaskName' already exists. Removing old task..."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create action to run PowerShell with the auto-start script
$Action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$AutoStartScript`""

# Create trigger to run at logon
$Trigger = New-ScheduledTaskTrigger -AtLogOn

# Create principal to run as current user
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

# Create settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

# Register the task
Register-ScheduledTask -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Principal $Principal `
    -Settings $Settings `
    -Description "Auto-start Local Nexus Controller and all registered services on Windows startup"

Write-Host ""
Write-Host "SUCCESS! Local Nexus Controller will now start automatically when you log in."
Write-Host ""
Write-Host "Task name: $TaskName"
Write-Host "To disable: Run tools\disable_windows_startup.ps1"
Write-Host "To view in Task Scheduler: taskschd.msc"
