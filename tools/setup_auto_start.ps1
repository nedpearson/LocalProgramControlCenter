# Local Nexus Controller - Auto-Start Setup Script
# This script configures Windows to automatically start the controller on boot

# Require administrator privileges
#Requires -RunAsAdministrator

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Local Nexus Controller - Auto-Start Setup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Get the project directory (parent of tools folder)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir

Write-Host "Project Directory: $ProjectDir" -ForegroundColor Yellow
Write-Host ""

# Verify project files exist
if (-not (Test-Path "$ProjectDir\package.json")) {
    Write-Host "ERROR: package.json not found in $ProjectDir" -ForegroundColor Red
    Write-Host "Make sure you're running this script from the tools folder" -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Create a batch file that will run npm run dev
$BatchFile = "$ProjectDir\tools\start_nexus_on_boot.bat"
$BatchContent = @"
@echo off
REM Auto-generated startup script for Local Nexus Controller
cd /d "$ProjectDir"
npm run dev
"@

Write-Host "Creating startup batch file..." -ForegroundColor Green
Set-Content -Path $BatchFile -Value $BatchContent -Force
Write-Host "✓ Created: $BatchFile" -ForegroundColor Green
Write-Host ""

# Task Scheduler configuration
$TaskName = "Local Nexus Controller"
$TaskDescription = "Automatically starts Local Nexus Controller on Windows startup"

Write-Host "Configuring Windows Task Scheduler..." -ForegroundColor Green
Write-Host ""

# Remove existing task if it exists
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Write-Host "Removing existing task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create the scheduled task action
$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$BatchFile`"" -WorkingDirectory $ProjectDir

# Create the trigger (at logon)
$Trigger = New-ScheduledTaskTrigger -AtLogon

# Create the principal (run as current user)
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

# Create the settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable:$false

# Register the scheduled task
try {
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Description $TaskDescription -Force | Out-Null
    Write-Host "✓ Task registered successfully!" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "✗ Failed to register task: $_" -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Verify the task was created
$Task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($Task) {
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "SUCCESS! Auto-start is now configured." -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Details:" -ForegroundColor Cyan
    Write-Host "  Name: $TaskName"
    Write-Host "  Status: $($Task.State)"
    Write-Host "  Trigger: At user logon"
    Write-Host "  Action: Start Local Nexus Controller"
    Write-Host ""
    Write-Host "The controller will automatically start when you log in to Windows." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To disable auto-start, run:" -ForegroundColor Cyan
    Write-Host "  tools\disable_auto_start.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "To test the task now, run:" -ForegroundColor Cyan
    Write-Host "  Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "✗ Task verification failed" -ForegroundColor Red
    Write-Host ""
}

Read-Host "Press Enter to exit"
