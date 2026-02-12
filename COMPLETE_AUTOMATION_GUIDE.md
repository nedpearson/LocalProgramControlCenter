# Complete Automation Guide

## One-Click Setup

**Double-click this file to configure everything:**
```
SETUP_COMPLETE_AUTOMATION.bat
```

That's it! Everything else is automatic.

---

## What Gets Configured

### 1. Service Auto-Start ✓
**Already Enabled** in your `.env`:
```env
LOCAL_NEXUS_AUTO_START_ALL_ON_BOOT=true
```

**What it does:**
- All services with `start_command` auto-start when controller starts
- Logs saved to `data/logs/`
- Status visible in dashboard

### 2. Windows Auto-Start
**Configured by:** `SETUP_COMPLETE_AUTOMATION.bat`

**What it does:**
- Controller starts automatically when you log in to Windows
- Runs in background
- Waits for network to be ready

### 3. Browser Auto-Open ✓
**Already Enabled** in your `.env`:
```env
LOCAL_NEXUS_OPEN_BROWSER=true
```

**What it does:**
- Dashboard automatically opens in your browser
- URL: http://localhost:5010
- Shows all running services

---

## Complete Boot Sequence

When you restart Windows and log in:

```
Windows Boot
    ↓
User Login
    ↓
Task Scheduler triggers
    ↓
Controller starts (tools/start_nexus_on_boot.bat)
    ↓
Controller initializes
    ↓
Auto-discovery scans C:\Users\nedpe\Desktop\Repositories
    ↓
File watcher starts monitoring C:\Users\nedpe\Desktop
    ↓
Service auto-start begins
    ↓
╔════════════════════════════════════╗
║ Auto-starting X service(s)         ║
╠════════════════════════════════════╣
║   Starting: Service 1... ✓ Started ║
║   Starting: Service 2... ✓ Started ║
║   Starting: Service 3... ✓ Started ║
╚════════════════════════════════════╝
    ↓
Browser opens to http://localhost:5010
    ↓
Dashboard shows all services running (green status)
    ↓
✓ DONE - Everything is running!
```

**Total time:** 30-60 seconds after login

**Zero manual steps required!**

---

## Setup Steps

### Step 1: Run Setup Script

**Double-click:**
```
SETUP_COMPLETE_AUTOMATION.bat
```

**What it does:**
1. Verifies service auto-start is enabled in `.env`
2. Launches Windows auto-start setup (requires admin)
3. Creates Task Scheduler task
4. Creates startup batch file
5. Verifies everything is configured

**Expected output:**
```
============================================================
SUCCESS! Complete Automation is Now Configured
============================================================
```

### Step 2: Test It (Optional)

**Manual test:**
```cmd
start.bat
```

Should show:
- Controller starts
- "Auto-starting X service(s)" message
- ✓ Started for each service
- Browser opens to dashboard

**Full automation test:**
1. Log out of Windows
2. Log back in
3. Wait 30-60 seconds
4. Dashboard should open automatically
5. All services should be running

---

## Verification Checklist

After running `SETUP_COMPLETE_AUTOMATION.bat`:

- [ ] Terminal shows "SUCCESS! Complete Automation is Now Configured"
- [ ] Task Scheduler has task named "Local Nexus Controller"
- [ ] File exists: `tools\start_nexus_on_boot.bat`
- [ ] `.env` has `LOCAL_NEXUS_AUTO_START_ALL_ON_BOOT=true`
- [ ] `.env` has `LOCAL_NEXUS_OPEN_BROWSER=true`

**Verify Windows auto-start:**
```cmd
schtasks /query /tn "Local Nexus Controller"
```

Should show task details.

**Verify service auto-start:**
```cmd
CHECK_AUTO_START.bat
```

Should show "Auto-start is ENABLED".

---

## What Happens on Every Boot

### Phase 1: Windows Startup (0-10 seconds)
- Windows boots
- User logs in
- Desktop appears
- Task Scheduler activates

### Phase 2: Controller Startup (10-20 seconds)
- Task Scheduler runs startup task
- Controller process starts
- Database initializes
- Auto-discovery scans repositories folder
- File watcher starts

### Phase 3: Service Startup (20-40 seconds)
- Each service with `start_command` starts
- Process manager launches commands
- Logs begin capturing output
- Status updates in database

### Phase 4: Dashboard Opens (40-60 seconds)
- Browser window opens automatically
- Dashboard loads at http://localhost:5010
- Shows all services with green "Running" status
- Ready to use!

---

## Configuration Files

### `.env` (Service Configuration)
```env
# Service auto-start
LOCAL_NEXUS_AUTO_START_ALL_ON_BOOT=true

# Browser auto-open
LOCAL_NEXUS_OPEN_BROWSER=true

# Auto-discovery
LOCAL_NEXUS_AUTO_DISCOVERY_ENABLED=true
LOCAL_NEXUS_REPOSITORIES_FOLDER=C:\Users\nedpe\Desktop\Repositories

# File watcher
LOCAL_NEXUS_FILE_WATCHER_ENABLED=true
LOCAL_NEXUS_FILE_WATCHER_FOLDER=C:\Users\nedpe\Desktop
```

### Task Scheduler (Windows Auto-Start)
- **Task Name:** Local Nexus Controller
- **Trigger:** At user logon
- **Action:** Run `tools\start_nexus_on_boot.bat`
- **User:** Your Windows account
- **Run Level:** Highest privileges

### Startup Batch File
**Location:** `tools\start_nexus_on_boot.bat`

**Contents:**
```batch
@echo off
cd /d "C:\path\to\your\project"
npm run dev
```

---

## Managing Automation

### Disable Everything
```cmd
tools\DISABLE_AUTO_START.bat
```

This removes:
- Windows Task Scheduler task
- Startup batch file

Service auto-start remains in `.env` but won't run if controller isn't started.

### Disable Only Service Auto-Start

Edit `.env`:
```env
LOCAL_NEXUS_AUTO_START_ALL_ON_BOOT=false
```

Controller still auto-starts on boot, but services don't.

### Disable Only Windows Auto-Start

```cmd
tools\DISABLE_AUTO_START.bat
```

Services still auto-start, but only when you manually run controller.

### Disable Browser Auto-Open

Edit `.env`:
```env
LOCAL_NEXUS_OPEN_BROWSER=false
```

Controller and services still auto-start, but browser doesn't open.

---

## Logs and Monitoring

### Controller Logs
**Windows Event Viewer:**
- Open Event Viewer
- Windows Logs → Application
- Look for entries from "Task Scheduler" or "Local Nexus Controller"

### Service Logs
**File location:**
```
data/logs/
```

**Each service has:**
- `ServiceName-abc123.log` - All output from the service
- Auto-rotated to prevent huge files

**View in dashboard:**
1. Go to http://localhost:5010
2. Click "Services"
3. Click service name
4. Scroll to "Logs" section

### Check What's Running

**Task Manager:**
1. Press Ctrl+Shift+Esc
2. Look for:
   - `python.exe` - Controller and Python services
   - `node.exe` - Node services
   - Other runtimes

**Dashboard:**
- http://localhost:5010 → Services page
- Green "Running" = Service is up
- Red "Error" = Service failed
- Gray "Stopped" = Service not started

---

## Troubleshooting

### Services Not Auto-Starting

**Check logs:**
```
data/logs/ServiceName-abc123.log
```

**Common issues:**
- Missing `start_command` on service
- Wrong working directory
- Dependencies not installed
- Port already in use
- Runtime not found (Python, Node, etc.)

**Fix:**
1. Go to dashboard
2. Click service name
3. Check "Last Error" field
4. Fix the issue
5. Restart controller

### Controller Not Auto-Starting

**Verify task exists:**
```cmd
schtasks /query /tn "Local Nexus Controller"
```

**If missing:**
```cmd
SETUP_COMPLETE_AUTOMATION.bat
```

**Check task history:**
1. Open Task Scheduler
2. Find "Local Nexus Controller"
3. Right-click → Properties
4. History tab

### Browser Not Opening

**Check .env:**
```env
LOCAL_NEXUS_OPEN_BROWSER=true
```

**Manual open:**
- http://localhost:5010

### Task Scheduler Says "Running" But Nothing Happens

**Kill and restart:**
```cmd
taskkill /F /IM python.exe
taskkill /F /IM node.exe
```

Then:
```cmd
start.bat
```

### Getting "ModuleNotFoundError"

**Install dependencies:**
```cmd
pip install -r requirements.txt
```

Or for auto-install:
```cmd
npm run dev
```

---

## Advanced Configuration

### Delayed Startup

To wait longer for system to be ready, edit the Task Scheduler task:

1. Open Task Scheduler
2. Find "Local Nexus Controller"
3. Right-click → Properties
4. Triggers tab → Edit
5. Advanced settings
6. "Delay task for:" 30 seconds (or more)

### Start Only on AC Power

1. Task Scheduler → Properties
2. Conditions tab
3. Check "Start only if computer is on AC power"

### Restart on Failure

1. Task Scheduler → Properties
2. Settings tab
3. "If the task fails, restart every:" 1 minute
4. "Attempt to restart up to:" 3 times

---

## Testing Checklist

### Test 1: Manual Start
```cmd
start.bat
```

**Expected:**
- Controller starts
- Terminal shows "Auto-starting X service(s)"
- ✓ Started for each service
- Browser opens
- Dashboard shows green statuses

### Test 2: Restart Controller
1. Close controller (Ctrl+C or close window)
2. Run `start.bat` again
3. Should auto-start services again

### Test 3: Windows Restart
1. Restart computer
2. Log in
3. Wait 60 seconds
4. Dashboard should open automatically
5. All services should be running

### Test 4: Check Logs
```
Open: data/logs/
```

Should see log files for each service.

### Test 5: Stop and Start Service
1. Dashboard → Services → Click service → Stop
2. Restart controller
3. Service should auto-start again

---

## What If Something Goes Wrong?

### Quick Reset

1. Disable auto-start:
   ```cmd
   tools\DISABLE_AUTO_START.bat
   ```

2. Fix the issue (check logs, fix services)

3. Re-enable:
   ```cmd
   SETUP_COMPLETE_AUTOMATION.bat
   ```

### Start Fresh

1. Remove all services from dashboard
2. Disable Windows auto-start
3. Verify `.env` settings
4. Add services back with correct configs
5. Test manually first
6. Then enable Windows auto-start

### Get Help

**Check documentation:**
- `AUTO_START_TROUBLESHOOTING.md` - Service auto-start issues
- `AUTO_START_STATUS.md` - Current configuration status
- `START_HERE_AFTER_REBOOT.md` - Boot errors
- `QUICK_FIX.md` - Common fixes

**Run diagnostics:**
```cmd
CHECK_AUTO_START.bat
```

---

## Summary

Complete automation requires:

1. ✅ **Service auto-start** - Already enabled in `.env`
2. ✅ **Browser auto-open** - Already enabled in `.env`
3. ⚙️ **Windows auto-start** - Run `SETUP_COMPLETE_AUTOMATION.bat`

After setup:
- Restart Windows
- Controller auto-starts
- Services auto-start
- Browser opens
- Dashboard shows everything running
- **Zero manual steps!**

---

## Quick Command Reference

| Task | Command |
|------|---------|
| Complete setup | Double-click `SETUP_COMPLETE_AUTOMATION.bat` |
| Manual start | Double-click `start.bat` |
| Check status | Double-click `CHECK_AUTO_START.bat` |
| Disable automation | `tools\DISABLE_AUTO_START.bat` |
| View logs | Open `data/logs/` folder |
| Open dashboard | http://localhost:5010 |
| Check task | `schtasks /query /tn "Local Nexus Controller"` |

---

**You're ready for complete automation!**

Just double-click `SETUP_COMPLETE_AUTOMATION.bat` and follow the prompts.
