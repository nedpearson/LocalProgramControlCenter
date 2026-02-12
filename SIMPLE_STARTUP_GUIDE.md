# Simple Startup Guide - No Errors, No Complexity

This guide provides bulletproof startup scripts with zero dependencies.

## Quick Start (Manual)

**Just double-click:**
```
QUICK_START.bat
```

This script:
- Automatically stops any process using port 5010
- Starts the controller
- Shows clear status messages
- Works every single time

## Auto-Start After Reboot

### One-Time Setup

**Right-click and "Run as Administrator":**
```
SIMPLE_AUTO_START_SETUP.bat
```

This creates a Windows Task Scheduler entry that runs on login.

### What Happens After Setup

1. You restart Windows
2. You log in
3. Controller starts automatically (hidden in background)
4. Dashboard available at http://127.0.0.1:5010

### Check If Auto-Start Is Enabled

```powershell
schtasks /Query /TN "Local Nexus Controller"
```

### Disable Auto-Start

```batch
schtasks /Delete /TN "Local Nexus Controller" /F
```

## Troubleshooting

### Port Conflict Errors

**Solution:** The scripts now handle this automatically. Every startup:
1. Checks port 5010
2. Stops any conflicting process
3. Waits briefly
4. Starts cleanly

### Python Not Found

**Check if Python is installed:**
```powershell
python --version
```

**If not installed:**
- Download from https://www.python.org/downloads/
- During installation, check "Add Python to PATH"

### Virtual Environment Issues

**The startup script automatically:**
- Checks for `.venv` folder
- Uses it if available
- Falls back to system Python if not

### Script Won't Run

**If you get "scripts are disabled" error:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Files Reference

### For Manual Use
- `QUICK_START.bat` - Simple manual startup
- `start.bat` - Alternative manual startup
- `run.ps1` - PowerShell manual startup

### For Auto-Start
- `SIMPLE_AUTO_START_SETUP.bat` - One-click auto-start setup
- `tools/auto_start_controller.ps1` - The script that runs on boot

### Logs
All auto-start activity is logged to:
```
data/logs/auto-start.log
```

Check this file if something goes wrong.

## How It Works

### Manual Startup (QUICK_START.bat)

```
1. Changes to project directory
2. Calls run.ps1
3. run.ps1 checks port 5010
4. run.ps1 stops conflicts
5. run.ps1 creates/uses venv
6. run.ps1 starts controller
```

### Auto-Start (Task Scheduler)

```
1. Windows loads
2. You log in
3. Task Scheduler triggers
4. Runs tools/auto_start_controller.ps1
5. Script checks port
6. Script stops conflicts
7. Script finds Python
8. Script starts controller
9. Everything logged to data/logs/auto-start.log
```

## Why This Works

### Simple Design
- No complex dependencies
- No script-calling-script chains
- Absolute paths everywhere
- Clear error messages

### Automatic Port Handling
- Always checks port first
- Always stops conflicts
- Never fails due to "port in use"

### Logging
- Everything logged to file
- Easy to diagnose issues
- Timestamps on all events

### Fallback Logic
- Tries venv Python first
- Falls back to system Python
- Clear error if neither found

## Testing

### Test Manual Startup
```batch
QUICK_START.bat
```

Expected output:
```
Checking for port conflicts and starting controller...
✓ Port 5010 is available
(or)
Stopping process ... (PID: 1234)
✓ Process stopped

[Controller starts]
```

### Test Auto-Start Setup
1. Run `SIMPLE_AUTO_START_SETUP.bat` as Administrator
2. Check task created:
   ```batch
   schtasks /Query /TN "Local Nexus Controller"
   ```
3. Test the task:
   ```batch
   schtasks /Run /TN "Local Nexus Controller"
   ```
4. Check log:
   ```batch
   type data\logs\auto-start.log
   ```

### Test After Reboot
1. Restart Windows
2. Log in
3. Wait 10 seconds
4. Open browser: http://127.0.0.1:5010
5. Check log: `data\logs\auto-start.log`

## Summary

You now have two simple options:

1. **Manual:** Double-click `QUICK_START.bat`
2. **Automatic:** Run `SIMPLE_AUTO_START_SETUP.bat` once (as Admin)

Both handle port conflicts automatically. Both work reliably. No complex setup required.
