# Clean up old startup methods
# This removes any old/broken startup shortcuts and scripts

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Local Nexus Controller - Cleanup Old Startup Methods" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$cleaned = 0

# Check Windows Startup folder
$StartupFolder = [System.Environment]::GetFolderPath('Startup')
Write-Host "Checking Startup folder: $StartupFolder" -ForegroundColor Yellow
Write-Host ""

# Look for any shortcuts related to Local Nexus Controller
$shortcuts = Get-ChildItem -Path $StartupFolder -Filter "*.lnk" -ErrorAction SilentlyContinue
foreach ($shortcut in $shortcuts) {
    $shell = New-Object -ComObject WScript.Shell
    $link = $shell.CreateShortcut($shortcut.FullName)

    if ($link.TargetPath -like "*local*nexus*" -or
        $link.TargetPath -like "*LocalProgramController*" -or
        $link.Arguments -like "*local*nexus*" -or
        $link.Arguments -like "*start_dashboard_widget*") {

        Write-Host "Found old shortcut: $($shortcut.Name)" -ForegroundColor Yellow
        Write-Host "  Target: $($link.TargetPath)" -ForegroundColor Gray
        Write-Host "  Arguments: $($link.Arguments)" -ForegroundColor Gray

        $confirm = Read-Host "Remove this shortcut? (Y/N)"
        if ($confirm -eq "Y" -or $confirm -eq "y") {
            Remove-Item $shortcut.FullName -Force
            Write-Host "  ✓ Removed" -ForegroundColor Green
            $cleaned++
        } else {
            Write-Host "  Skipped" -ForegroundColor Gray
        }
        Write-Host ""
    }
}

# Check for VBS files in startup
$vbsFiles = Get-ChildItem -Path $StartupFolder -Filter "*.vbs" -ErrorAction SilentlyContinue
foreach ($vbs in $vbsFiles) {
    $content = Get-Content $vbs.FullName -Raw
    if ($content -like "*local*nexus*" -or $content -like "*LocalProgramController*") {
        Write-Host "Found old VBS script: $($vbs.Name)" -ForegroundColor Yellow

        $confirm = Read-Host "Remove this script? (Y/N)"
        if ($confirm -eq "Y" -or $confirm -eq "y") {
            Remove-Item $vbs.FullName -Force
            Write-Host "  ✓ Removed" -ForegroundColor Green
            $cleaned++
        } else {
            Write-Host "  Skipped" -ForegroundColor Gray
        }
        Write-Host ""
    }
}

# Check Task Scheduler for old tasks
Write-Host "Checking Task Scheduler..." -ForegroundColor Yellow
Write-Host ""

$oldTaskNames = @(
    "Local Nexus Controller - Widget",
    "LocalProgramController",
    "Start Dashboard Widget"
)

foreach ($taskName in $oldTaskNames) {
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($task) {
        Write-Host "Found old task: $taskName" -ForegroundColor Yellow
        Write-Host "  Status: $($task.State)" -ForegroundColor Gray

        $confirm = Read-Host "Remove this task? (Y/N)"
        if ($confirm -eq "Y" -or $confirm -eq "y") {
            Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
            Write-Host "  ✓ Removed" -ForegroundColor Green
            $cleaned++
        } else {
            Write-Host "  Skipped" -ForegroundColor Gray
        }
        Write-Host ""
    }
}

# Summary
Write-Host "============================================================" -ForegroundColor Cyan
if ($cleaned -gt 0) {
    Write-Host "✓ Cleaned up $cleaned old startup item(s)" -ForegroundColor Green
} else {
    Write-Host "No old startup items found" -ForegroundColor Yellow
}
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "You can now set up auto-start properly by running:" -ForegroundColor Cyan
Write-Host "  tools\ENABLE_AUTO_START.bat" -ForegroundColor White
Write-Host ""

Read-Host "Press Enter to exit"
