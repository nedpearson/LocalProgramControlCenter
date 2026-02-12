# ⚠️ START HERE - Fixing Your Startup Errors

## You're Seeing These Errors Because...

Based on your screenshot, you have 3 problems:

1. **Wrong directory** - You're in `C:\WINDOWS\system32` instead of your project folder
2. **Fake path** - `C:\path\to\local-nexus-controller` doesn't exist (it's an example from docs)
3. **Old broken startup** - There's an old widget script trying to run from the wrong location

**Let's fix all of this right now!**

---

## Step 1: Find Your Project Folder (30 seconds)

**You need to find where you actually saved this project.**

### Quick Method:
1. **Double-click this file:** `WHERE_AM_I.bat` (in this folder)
2. It will show you the project path
3. Copy that path - you'll need it!

### Alternative - Use Windows Search:
1. Press `Win` key
2. Type: `package.json local nexus`
3. Right-click result → "Open file location"

**Write down your actual path. It's probably something like:**
- `C:\Users\nedpe\LocalNexusController`
- `C:\Users\nedpe\Documents\GitHub\local-nexus-controller`
- `C:\Dev\local-nexus-controller`

---

## Step 2: Clean Up Old Broken Startup (2 minutes)

The errors at the bottom of your screenshot show old broken startup shortcuts.

### Fix It:

1. **Hold Shift** and **right-click** in your project folder (where this file is)
2. Click "Open PowerShell window here"
3. Run:
   ```powershell
   .\tools\cleanup_old_startup.ps1
   ```
4. Press `Y` to remove any old shortcuts it finds

This removes the broken widget startup causing those errors.

---

## Step 3: Set Up Auto-Start Correctly (1 minute)

Now let's configure auto-start properly:

### Option A: Double-Click Method (Easiest)
1. Go to the `tools` folder
2. **Double-click** `ENABLE_AUTO_START.bat`
3. Click "Yes" when asked for administrator access
4. Wait for "SUCCESS!" message

### Option B: PowerShell Method
In PowerShell (from your project folder):
```powershell
.\tools\setup_auto_start.ps1
```

---

## Step 4: Test It Works (1 minute)

### Test Manual Start First:
Double-click `start.bat` in your project folder.

**Expected:** Browser opens to http://localhost:5010

### Test Auto-Start:
1. Close everything
2. Log out of Windows
3. Log back in
4. Controller should start automatically!

---

## Don't Make These Mistakes:

### ❌ DON'T: Run commands from System32
```cmd
PS C:\WINDOWS\system32> start.bat
```
**This won't work!**

### ✅ DO: Navigate to your project first
```cmd
cd C:\Users\nedpe\LocalNexusController
start.bat
```

### ❌ DON'T: Use placeholder paths
```cmd
cd C:\path\to\local-nexus-controller
```
**This doesn't exist!**

### ✅ DO: Use YOUR actual path
```cmd
cd C:\Users\nedpe\LocalNexusController
```

---

## If You Just Want to Start Manually (No Auto-Start)

Don't want auto-start? Just want to run it yourself?

**Easy method:**
1. Navigate to your project folder in File Explorer
2. Double-click `start.bat`
3. Done!

**Command Prompt method:**
```cmd
cd C:\Users\nedpe\LocalNexusController
start.bat
```
(Replace with your actual path)

---

## Troubleshooting Common Issues

### "Python not found"
Install Python from https://python.org

Check "Add Python to PATH" during installation.

### "npm not found"
Install Node.js from https://nodejs.org

### "Execution policy" error in PowerShell
Run this first:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### "Access denied" when setting up auto-start
Right-click `ENABLE_AUTO_START.bat` → "Run as administrator"

---

## Understanding the Errors in Your Screenshot

### Top Window Errors:

**Error 1:**
```
Cannot find path 'C:\path\to\local-nexus-controller' because it does not exist
```
**Explanation:** You copied an example path from documentation. That's not a real path on your computer.

**Error 2:**
```
start.bat : The term 'start.bat' is not recognized
```
**Explanation:** You were in System32 directory. `start.bat` is in YOUR project folder, not System32.

### Bottom Window Errors:

```
[error 2147942402...start_dashboard_widget.ps1"]
The system cannot find the file specified
```

**Explanation:** You have an old broken shortcut in your Windows Startup folder trying to run a widget script that doesn't exist or is in the wrong location.

**Fix:** Run `tools\cleanup_old_startup.ps1` (Step 2 above)

---

## Quick Reference Card

| What You Want | What To Do |
|---------------|------------|
| Find project location | Double-click `WHERE_AM_I.bat` |
| Start manually | Double-click `start.bat` |
| Enable auto-start | Double-click `tools\ENABLE_AUTO_START.bat` |
| Clean up old broken startup | Run `tools\cleanup_old_startup.ps1` |
| Disable auto-start | Double-click `tools\DISABLE_AUTO_START.bat` |

---

## Final Checklist

- [ ] Found your actual project path (not the placeholder)
- [ ] Cleaned up old broken startup (`tools\cleanup_old_startup.ps1`)
- [ ] Enabled auto-start correctly (`tools\ENABLE_AUTO_START.bat`)
- [ ] Tested manual start (double-click `start.bat`)
- [ ] Tested auto-start (log out and back in)

---

## Still Stuck?

1. Double-click `WHERE_AM_I.bat` - shows your project path
2. Go to `tools` folder
3. Double-click `ENABLE_AUTO_START.bat`
4. Restart your computer

That's it! No more errors.

---

**Remember:** Always run commands FROM your project folder, not from System32!
