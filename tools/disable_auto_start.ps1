# Local Nexus Controller - Disable Auto-Start Script
# This script removes the Windows startup task

# Require administrator privileges
#Requires -RunAsAdministrator

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Local Nexus Controller - Disable Auto-Start" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$TaskName = "Local Nexus Controller"

# Check if task exists
$Task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($Task) {
    Write-Host "Found task: $TaskName" -ForegroundColor Yellow
    Write-Host "Status: $($Task.State)" -ForegroundColor Yellow
    Write-Host ""

    $Confirm = Read-Host "Do you want to remove this task? (Y/N)"

    if ($Confirm -eq "Y" -or $Confirm -eq "y") {
        try {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
            Write-Host ""
            Write-Host "✓ Auto-start disabled successfully!" -ForegroundColor Green
            Write-Host ""
            Write-Host "The controller will no longer start automatically on boot." -ForegroundColor Yellow
            Write-Host ""
            Write-Host "To re-enable auto-start, run:" -ForegroundColor Cyan
            Write-Host "  tools\setup_auto_start.ps1" -ForegroundColor White
            Write-Host ""
        } catch {
            Write-Host ""
            Write-Host "✗ Failed to remove task: $_" -ForegroundColor Red
            Write-Host ""
        }
    } else {
        Write-Host ""
        Write-Host "Operation cancelled." -ForegroundColor Yellow
        Write-Host ""
    }
} else {
    Write-Host "Task not found: $TaskName" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Auto-start is not currently configured." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To enable auto-start, run:" -ForegroundColor Cyan
    Write-Host "  tools\setup_auto_start.ps1" -ForegroundColor White
    Write-Host ""
}

Read-Host "Press Enter to exit"
