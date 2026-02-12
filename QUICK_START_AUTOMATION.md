# Quick Start - Complete Automation

## One-Click Setup

**Double-click this file:**
```
SETUP_COMPLETE_AUTOMATION.bat
```

Click "Yes" when asked for administrator access.

Wait for "SUCCESS!" message.

Done!

---

## What You Get

### On Every Windows Boot:
1. Controller starts automatically (30 seconds after login)
2. All services start automatically
3. Dashboard opens in browser
4. Everything ready to use!

### Zero Manual Steps
- No commands to run
- No buttons to click
- No waiting around

Just restart Windows and everything runs automatically.

---

## How to Test

### Test Now:
```cmd
start.bat
```

You should see:
```
============================================================
Auto-starting 3 service(s)
============================================================
  Starting: My Service... ✓ Started
  Starting: Another Service... ✓ Started
  Starting: Third Service... ✓ Started
============================================================
```

Dashboard opens automatically.

### Test Full Automation:
1. Restart Windows
2. Log in
3. Wait 60 seconds
4. Dashboard opens automatically
5. All services running!

---

## Status Check

**Quick diagnostic:**
```cmd
CHECK_AUTO_START.bat
```

Shows:
- Service auto-start: Enabled/Disabled
- Windows auto-start: Configured/Not configured
- Current settings

---

## Disable If Needed

**To turn off automation:**
```cmd
tools\DISABLE_AUTO_START.bat
```

This removes Windows auto-start but keeps service auto-start in `.env`.

To disable service auto-start too, edit `.env`:
```env
LOCAL_NEXUS_AUTO_START_ALL_ON_BOOT=false
```

---

## Troubleshooting

**If services don't start:**
- Check `data/logs/` for error messages
- Verify services have `start_command` defined
- See `AUTO_START_TROUBLESHOOTING.md`

**If controller doesn't start:**
- Check Task Scheduler for "Local Nexus Controller" task
- Run `SETUP_COMPLETE_AUTOMATION.bat` again

**If browser doesn't open:**
- Manually open: http://localhost:5010
- Or edit `.env`: `LOCAL_NEXUS_OPEN_BROWSER=true`

---

## Files Created

- `SETUP_COMPLETE_AUTOMATION.bat` - One-click setup
- `COMPLETE_AUTOMATION_GUIDE.md` - Complete documentation
- `AUTO_START_TROUBLESHOOTING.md` - Troubleshooting guide
- `CHECK_AUTO_START.bat` - Status checker
- `tools/start_nexus_on_boot.bat` - Startup script
- Windows Task Scheduler task - Auto-start trigger

---

## Summary

| Feature | Status |
|---------|--------|
| Service auto-start | ✅ Enabled |
| Browser auto-open | ✅ Enabled |
| Windows auto-start | ⚙️ Run setup script |

**Next step:** Double-click `SETUP_COMPLETE_AUTOMATION.bat`

**After setup:** Restart Windows to test!
