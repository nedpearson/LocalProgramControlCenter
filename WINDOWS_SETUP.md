# Windows Setup Guide

## Quick Fix for "EPERM: operation not permitted" Error

If you see an error like:
```
Error: EPERM: operation not permitted, mkdir 'C:\Windows\System32\node_modules\.vite\deps_temp_...'
```

**This means you're running the command from the wrong directory!**

### Solution

1. **Open Command Prompt or PowerShell**
2. **Navigate to the project directory**:
   ```cmd
   cd path\to\local-nexus-controller
   ```
3. **Run the startup script**:
   ```cmd
   start.bat
   ```

   OR use npm:
   ```cmd
   npm run dev
   ```

---

## Recommended Startup Methods for Windows

### Method 1: Use the Batch File (Easiest)

Double-click `start.bat` in the project folder, or run:
```cmd
start.bat
```

**Benefits:**
- Automatically changes to correct directory
- Checks Python installation
- Shows clear error messages
- Handles dependency installation

### Method 2: Use npm from Project Directory

1. Open Command Prompt or PowerShell
2. Navigate to project:
   ```cmd
   cd C:\path\to\local-nexus-controller
   ```
3. Run:
   ```cmd
   npm run dev
   ```

### Method 3: Direct Python Command

```cmd
cd C:\path\to\local-nexus-controller
python -m local_nexus_controller
```

---

## Common Windows Issues

### Issue 1: Running from System32

**Problem:** Command Prompt opens in `C:\Windows\System32` by default

**Symptoms:**
- Vite errors about System32 directories
- "EPERM: operation not permitted"
- Can't find project files

**Solution:**
1. Always `cd` to your project directory first
2. Or use the `start.bat` script which does this automatically

### Issue 2: Python Not Found

**Problem:** `python` command not recognized

**Solutions:**

A. **Check if Python is installed:**
   ```cmd
   python --version
   ```

   If not found, install from: https://www.python.org/downloads/

B. **Use `py` launcher instead:**
   ```cmd
   py --version
   py -m local_nexus_controller
   ```

C. **Add Python to PATH:**
   - Reinstall Python
   - Check "Add Python to PATH" during installation

### Issue 3: pip Not Available

**Problem:** `pip` command not working

**Solutions:**

Try these in order:
```cmd
pip install -r requirements.txt
python -m pip install -r requirements.txt
py -m pip install -r requirements.txt
pip3 install -r requirements.txt
```

The application will try all of these automatically!

### Issue 4: Permission Errors During Install

**Problem:** "Access is denied" when installing packages

**Solutions:**

A. **Use --user flag:**
   ```cmd
   pip install --user -r requirements.txt
   ```

B. **Run as Administrator:**
   - Right-click Command Prompt
   - Select "Run as administrator"
   - Navigate to project and run commands

C. **Use a virtual environment:**
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   python -m local_nexus_controller
   ```

---

## Recommended Setup for Windows

### One-Time Setup

1. **Install Python 3.10 or higher**
   - Download from https://www.python.org/downloads/
   - CHECK "Add Python to PATH" during installation

2. **Open PowerShell or Command Prompt**

3. **Navigate to project:**
   ```cmd
   cd C:\path\to\local-nexus-controller
   ```

4. **Install dependencies** (optional, auto-installs on first run):
   ```cmd
   pip install -r requirements.txt
   ```

### Daily Use

Just double-click `start.bat` or run:
```cmd
npm run dev
```

---

## Understanding the Vite Error

**Why does Vite show up in the errors?**

The Vite error in your screenshot is a red herring. It's happening because:

1. Your terminal was in the `C:\Windows\System32` directory
2. Some process (possibly the Bolt.new IDE) was trying to start
3. It tried to write temp files to System32 (not allowed)

**Local Nexus Controller doesn't use Vite.** It's a Python/FastAPI application with simple HTML templates.

The fix is to ensure you're running commands from the project directory, not System32.

---

## Verification Steps

After setup, verify everything works:

### 1. Check Python
```cmd
python --version
```
Should show: Python 3.10.0 or higher

### 2. Check Project Files
```cmd
dir
```
Should show: `app.py`, `requirements.txt`, `local_nexus_controller` folder

### 3. Test Import
```cmd
python -c "import sys; print(sys.executable)"
```
Should show path to your Python installation

### 4. Run Application
```cmd
start.bat
```
Or:
```cmd
npm run dev
```

Should see:
```
INFO:     Uvicorn running on http://0.0.0.0:5010
```

### 5. Open Browser
Visit: http://localhost:5010

You should see the Local Nexus Controller dashboard!

---

## PowerShell Execution Policy

If you get "execution policy" errors in PowerShell:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try running again.

---

## Environment Variables

The application uses these environment variables (optional):

```env
LOCAL_NEXUS_PORT=5010
LOCAL_NEXUS_HOST=0.0.0.0
LOCAL_NEXUS_OPEN_BROWSER=true
LOCAL_NEXUS_RELOAD=true
```

Create a `.env` file in the project root to customize these.

---

## Still Having Issues?

1. **Check you're in the correct directory:**
   ```cmd
   cd
   ```
   Should show your project path, not System32

2. **Try the batch file:**
   ```cmd
   start.bat
   ```

3. **Check the full error message** and see which method failed

4. **Manual installation:**
   ```cmd
   cd C:\path\to\local-nexus-controller
   pip install fastapi uvicorn sqlmodel jinja2 python-dotenv psutil
   python -m local_nexus_controller
   ```

5. **Check Python path:**
   ```cmd
   where python
   ```

If all else fails, try using a Python virtual environment (see Issue 4 above).

---

## Success Indicators

When everything works, you'll see:

```
INFO:     Will watch for changes in these directories: [...]
INFO:     Uvicorn running on http://0.0.0.0:5010 (Press CTRL+C to quit)
INFO:     Started reloader process [...]
INFO:     Started server process [...]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

Then open http://localhost:5010 in your browser!
