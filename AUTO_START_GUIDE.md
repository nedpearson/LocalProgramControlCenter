# Auto-Start Setup Guide

This guide shows you how to configure Local Nexus Controller to automatically start when Windows boots.

---

## Quick Setup (Recommended)

### Enable Auto-Start

1. Open the `tools` folder in your project
2. **Double-click** `ENABLE_AUTO_START.bat`
3. Click "Yes" when prompted for administrator access
4. Follow the prompts
5. Done! The controller will now start automatically on boot

### Disable Auto-Start

1. Open the `tools` folder in your project
2. **Double-click** `DISABLE_AUTO_START.bat`
3. Click "Yes" when prompted for administrator access
4. Confirm removal when asked
5. Done! Auto-start is disabled

---

## What Gets Configured

When you enable auto-start, the setup script:

1. ✅ Creates a Windows Task Scheduler task
2. ✅ Configures it to run at user logon
3. ✅ Sets the correct working directory (your project folder)
4. ✅ Runs `npm run dev` automatically
5. ✅ Handles dependencies installation on first run
6. ✅ Opens your browser to http://localhost:5010

---

## How It Works

### The Setup Process

1. **Task Scheduler Entry**
   - Task Name: "Local Nexus Controller"
   - Trigger: At user logon
   - Action: Run `npm run dev` from project directory
   - User: Your Windows account
   - Privilege Level: Highest (to access ports)

2. **Startup Script**
   - Location: `tools/start_nexus_on_boot.bat`
   - Changes to correct directory
   - Runs `npm run dev`
   - Keeps window minimized

3. **Application Startup**
   - Auto-installs dependencies if needed
   - Starts FastAPI server on port 5010
   - Opens dashboard in browser
   - Runs in background

---

## Verification

### Check If Auto-Start Is Enabled

**Method 1: Task Scheduler GUI**
1. Press `Win + R`
2. Type `taskschd.msc` and press Enter
3. Look for "Local Nexus Controller" in the task list
4. Status should show "Ready"

**Method 2: PowerShell**
```powershell
Get-ScheduledTask -TaskName "Local Nexus Controller"
```

### Test Auto-Start Manually

**Option A: Run the task now**
```powershell
Start-ScheduledTask -TaskName "Local Nexus Controller"
```

**Option B: Log out and log back in**
1. Save all your work
2. Log out of Windows
3. Log back in
4. The controller should start automatically

---

## Troubleshooting

### Issue: "Access Denied" Error

**Cause:** Script needs administrator privileges

**Solution:**
- Right-click the .bat file
- Select "Run as administrator"

### Issue: Task Created But Nothing Happens on Startup

**Check 1: Verify task is enabled**
```powershell
Get-ScheduledTask -TaskName "Local Nexus Controller" | Select-Object State
```
Should show: `Ready`

**Check 2: Check task history**
1. Open Task Scheduler (`taskschd.msc`)
2. Find "Local Nexus Controller"
3. Click the "History" tab
4. Look for errors

**Check 3: Test the batch file manually**
```cmd
cd tools
start_nexus_on_boot.bat
```

### Issue: PowerShell Execution Policy Error

**Symptom:** "Scripts are disabled on this system"

**Solution:**
Run this in PowerShell as Administrator:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try again.

### Issue: Node/npm Not Found

**Cause:** Node.js not in system PATH for scheduled tasks

**Solution A: Add Node to System PATH**
1. Search for "Environment Variables" in Windows
2. Edit "Path" under System variables
3. Add Node.js installation path (e.g., `C:\Program Files\nodejs`)
4. Restart computer

**Solution B: Modify startup script to use full path**
Edit `tools/start_nexus_on_boot.bat`:
```batch
@echo off
cd /d "C:\full\path\to\project"
"C:\Program Files\nodejs\npm.cmd" run dev
```

### Issue: Python Not Found

**Cause:** Python not in system PATH

**Solution:** Same as Node issue above - add Python to system PATH

### Issue: Multiple Instances Running

**Symptom:** Port 5010 already in use

**Check what's running:**
```powershell
Get-Process | Where-Object {$_.ProcessName -like "*python*"}
```

**Kill existing processes:**
```powershell
Stop-Process -Name python -Force
```

**Or use the dashboard:**
Visit http://localhost:5010 and stop services from there

---

## Advanced Configuration

### Change Startup Delay

Edit the task in Task Scheduler:
1. Open Task Scheduler
2. Find "Local Nexus Controller"
3. Right-click → Properties
4. Triggers tab → Edit
5. Check "Delay task for:" and set delay (e.g., 30 seconds)

### Run Only When Connected to Specific Network

Edit the task:
1. Conditions tab
2. Check "Start only if the following network connection is available"
3. Select your network

### Change Port or Other Settings

Edit `.env` file in project root:
```env
LOCAL_NEXUS_PORT=5010
LOCAL_NEXUS_HOST=0.0.0.0
LOCAL_NEXUS_OPEN_BROWSER=true
```

---

## Files Created by Setup

```
tools/
├── ENABLE_AUTO_START.bat          # Double-click to enable
├── DISABLE_AUTO_START.bat         # Double-click to disable
├── setup_auto_start.ps1           # PowerShell setup script
├── disable_auto_start.ps1         # PowerShell removal script
├── start_nexus_on_boot.bat        # Auto-generated startup script
└── start_on_boot.vbs              # Alternative VBS launcher
```

---

## Alternative: Startup Folder Method (Not Recommended)

If Task Scheduler doesn't work, you can use the Startup folder:

1. Press `Win + R`
2. Type `shell:startup` and press Enter
3. Create a shortcut to `tools/start_nexus_on_boot.bat`
4. Restart to test

**Note:** This method is less reliable than Task Scheduler.

---

## Security Considerations

### Why Administrator Access Is Needed

- **Port Binding:** Opening port 5010 requires elevated privileges
- **Task Scheduler:** Creating system tasks requires admin rights
- **Process Management:** Starting/stopping services needs permissions

### What Gets Accessed

- ✅ Task Scheduler (to create startup task)
- ✅ Project directory (to run the application)
- ✅ Network port 5010 (for web interface)
- ❌ No system files are modified
- ❌ No registry changes outside Task Scheduler
- ❌ No data collection or external connections

### Removing Everything

To completely remove auto-start:

1. Run `DISABLE_AUTO_START.bat`
2. Delete `tools/start_nexus_on_boot.bat` (optional)
3. Verify in Task Scheduler that task is gone

---

## FAQ

### Q: Will this slow down my computer startup?

**A:** Minimal impact. The task starts after you log in, not during Windows boot. The actual application takes 2-3 seconds to start.

### Q: Can I change what port it uses?

**A:** Yes, edit the `.env` file:
```env
LOCAL_NEXUS_PORT=8080
```

### Q: Will it start if I'm not logged in?

**A:** No. The task is configured to run at user logon, so you must be logged into Windows.

### Q: Can I start it without opening the browser?

**A:** Yes, edit `.env`:
```env
LOCAL_NEXUS_OPEN_BROWSER=false
```

### Q: How do I see the console output?

**A:** The console window runs minimized. To see output:
1. Open Task Manager
2. Find "cmd.exe" or "python.exe"
3. Right-click → Bring to front

Or check logs at: http://localhost:5010

### Q: Can I run multiple instances?

**A:** Not on the same port. Change the port in `.env` for additional instances.

### Q: Does this work with Python virtual environments?

**A:** Yes, but modify `start_nexus_on_boot.bat` to activate the venv first:
```batch
@echo off
cd /d "C:\path\to\project"
call venv\Scripts\activate
npm run dev
```

---

## Summary

**To enable auto-start:**
```
1. Double-click: tools/ENABLE_AUTO_START.bat
2. Click "Yes" for admin access
3. Done!
```

**To disable auto-start:**
```
1. Double-click: tools/DISABLE_AUTO_START.bat
2. Click "Yes" for admin access
3. Confirm removal
4. Done!
```

**To verify it's working:**
```
1. Log out of Windows
2. Log back in
3. Browser should open to http://localhost:5010
```

That's it! Your Local Nexus Controller will now start automatically every time you log into Windows.
