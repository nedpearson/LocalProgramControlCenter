# Quick Fix for Your Startup Errors

## The Problem (From Your Screenshot)

You're seeing these errors because:

1. ❌ **You're in the wrong directory** (`C:\WINDOWS\system32`)
2. ❌ **The path `C:\path\to\local-nexus-controller` doesn't exist** (it's just an example)
3. ❌ **Old widget startup scripts are broken** and trying to run from wrong locations

---

## Fix It Right Now - 3 Steps

### Step 1: Find Your ACTUAL Project Path

Open Windows Explorer and navigate to where you saved Local Nexus Controller.

**Your project path is probably something like:**
- `C:\Users\nedpe\LocalNexusController`
- `C:\Users\nedpe\Documents\LocalNexusController`
- `C:\Users\nedpe\Projects\local-nexus-controller`
- `C:\Dev\local-nexus-controller`

**Find the folder that contains these files:**
- `package.json`
- `requirements.txt`
- `app.py`
- `tools` folder

**Write down or copy this path - you'll need it!**

---

### Step 2: Clean Up Old Broken Startup Scripts

1. **Open PowerShell in your project directory:**
   - In Windows Explorer, navigate to your actual project folder
   - Hold Shift and right-click in the folder
   - Select "Open PowerShell window here"

2. **Run the cleanup script:**
   ```powershell
   .\tools\cleanup_old_startup.ps1
   ```

3. **Remove any old shortcuts it finds** (press Y when asked)

---

### Step 3: Set Up Auto-Start Correctly

**Still in the same PowerShell window** (in your project folder):

```powershell
.\tools\ENABLE_AUTO_START.bat
```

OR just **double-click** `ENABLE_AUTO_START.bat` in the `tools` folder.

When it asks for administrator access, click **Yes**.

---

## Alternative: Manual Start (No Auto-Start)

If you just want to start it manually each time:

### Method 1: Use File Explorer

1. Navigate to your project folder in Windows Explorer
2. Double-click `start.bat`

### Method 2: Use PowerShell/Command Prompt

```cmd
cd C:\YOUR\ACTUAL\PROJECT\PATH
start.bat
```

**Replace `C:\YOUR\ACTUAL\PROJECT\PATH` with your real path!**

For example:
```cmd
cd C:\Users\nedpe\LocalNexusController
start.bat
```

---

## Why You Got Those Errors

Looking at your screenshot:

### Error 1: "Cannot find path"
```
cd C:\path\to\local-nexus-controller
: Cannot find path 'C:\path\to\local-nexus-controller' because it does not exist.
```

**Cause:** `C:\path\to\local-nexus-controller` is a PLACEHOLDER in the documentation. You need to use YOUR actual path.

### Error 2: "start.bat not recognized"
```
start.bat : The term 'start.bat' is not recognized
```

**Cause:** You were in `C:\WINDOWS\system32`, not in the project folder. The `start.bat` file is in your project folder.

### Error 3: "File not specified" (bottom window)
```
[error 2147942402 (0x80070002) when launching ...start_dashboard_widget.ps1"]
The system cannot find the file specified.
```

**Cause:** Old broken startup shortcut in your Windows Startup folder pointing to wrong location.

**Fix:** Run the cleanup script from Step 2 above.

---

## How to Find Your Project Path

If you can't remember where you saved the project:

### Method 1: Search
1. Open Windows Search (Win key)
2. Type: `package.json local nexus`
3. Right-click the result → "Open file location"
4. This is your project folder!

### Method 2: Check Recent Folders
1. Open File Explorer
2. Look under "Recent" in the left sidebar
3. Find "local-nexus-controller" or similar

### Method 3: Check Common Locations
Open these in File Explorer:
- `C:\Users\nedpe\` (your user folder)
- `C:\Users\nedpe\Documents`
- `C:\Users\nedpe\Desktop`
- `C:\Dev`
- `C:\Projects`

---

## After You Fix Everything

### Test Manual Start
```cmd
cd C:\YOUR\ACTUAL\PATH
start.bat
```

Should open dashboard at http://localhost:5010

### Test Auto-Start
1. Close everything
2. Log out of Windows
3. Log back in
4. Controller should start automatically!

---

## Still Having Issues?

### Issue: PowerShell Execution Policy
If you get "scripts are disabled" error:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try again.

### Issue: Python Not Found
Install Python from https://python.org

Make sure to check "Add Python to PATH" during installation.

### Issue: npm Not Found
Install Node.js from https://nodejs.org

### Issue: Still Can't Find Project Folder
If you literally cannot find where you downloaded/cloned the project:

1. Download it again or clone from git
2. Save it to: `C:\Users\nedpe\LocalNexusController`
3. Follow steps above using this path

---

## Quick Command Reference

**Find where you are:**
```cmd
cd
```

**Go to your project:**
```cmd
cd C:\Users\nedpe\LocalNexusController
```
*(use your actual path)*

**Start manually:**
```cmd
start.bat
```

**Enable auto-start:**
```cmd
.\tools\ENABLE_AUTO_START.bat
```

**Clean up old broken startup:**
```cmd
.\tools\cleanup_old_startup.ps1
```

---

## Summary

1. ✅ Find your actual project folder path
2. ✅ Run `tools\cleanup_old_startup.ps1` from project folder
3. ✅ Run `tools\ENABLE_AUTO_START.bat`
4. ✅ Restart computer to test

That's it! No more errors.
