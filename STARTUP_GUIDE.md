# Startup Guide - Local Nexus Controller

## Quick Start

The Local Nexus Controller now has **automatic dependency installation** built in. Just run:

```bash
npm run dev
```

If dependencies are missing, they will be automatically installed on first run.

---

## What Happens on Startup

### 1. Dependency Check
When you run `npm run dev`, the application checks if `uvicorn` is installed.

### 2. Auto-Install (if needed)
If dependencies are missing:
- The application automatically runs `pip install -r requirements.txt`
- Tries `--break-system-packages` flag first
- Falls back to `--user` flag if needed
- Shows clear messages about what's happening

### 3. Restart Prompt
If dependencies were just installed, you'll see:
```
✓ Dependencies installed successfully
Please restart the application.
```

Just run `npm run dev` again and it will start normally.

---

## Startup Methods

### Method 1: npm (Recommended)
```bash
npm run dev
```

**Features:**
- Automatic dependency installation via `predev` hook
- Works in any environment (Bolt.new, local, Cursor)
- Shows clear error messages

### Method 2: Direct Python
```bash
python3 -m local_nexus_controller
```

**Features:**
- Checks for uvicorn on startup
- Auto-installs dependencies if missing
- Shows installation progress

### Method 3: Shell Script (Local only)
```bash
./start.sh
```

**Features:**
- Checks prerequisites before starting
- Validates Python version
- Ensures data directories exist

---

## After Reboot

When you reboot your system or the Bolt.new environment refreshes:

1. **Dependencies Reset**: Python packages may need to be reinstalled
2. **Auto-Recovery**: The application detects this and installs them automatically
3. **No Manual Steps**: Just run `npm run dev` as usual

The first startup after a reboot will take a bit longer while dependencies install, but subsequent starts will be instant.

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'uvicorn'"

**This is now handled automatically!** The application will:
1. Detect the missing module
2. Install all dependencies
3. Prompt you to restart

If auto-install fails, you'll see clear instructions for manual installation.

### Manual Installation (if needed)

If automatic installation doesn't work:

```bash
# Try method 1 (usually works)
python3 -m pip install --break-system-packages -r requirements.txt

# Or method 2 (user install)
python3 -m pip install --user -r requirements.txt

# Or method 3 (simple)
pip3 install -r requirements.txt
```

### Dependencies Installed But Still Getting Error

Check which Python is being used:

```bash
which python3
python3 --version
python3 -c "import uvicorn; print('✓ uvicorn found')"
```

If uvicorn is found, try:
```bash
python3 -m uvicorn local_nexus_controller.main:app --host 0.0.0.0 --port 5010
```

---

## Environment-Specific Notes

### Bolt.new / StackBlitz
- Environment may reset between sessions
- Dependencies auto-install on first run after reset
- Takes 30-60 seconds for first startup
- Normal after that

### Local Development
- Dependencies persist between runs
- Only installs once unless you delete them
- Fastest startup method

### Cursor / VS Code
- Uses your local Python environment
- Dependencies persist
- May need to select correct Python interpreter

---

## Build Script

The `npm run build` command:
1. Ensures dependencies are installed
2. Verifies the application can import correctly
3. Shows `✓ Application ready` when successful

```bash
npm run build
```

Use this to verify everything is set up correctly without starting the server.

---

## What Gets Installed

From `requirements.txt`:
- `fastapi` - Web framework
- `uvicorn[standard]` - ASGI server
- `sqlmodel` - Database ORM
- `SQLAlchemy` - Database toolkit
- `jinja2` - Template engine
- `python-dotenv` - Environment variables
- `psutil` - Process management

Total install size: ~50MB

---

## Advanced Configuration

### Disable Auto-Browser Opening

Set in `.env`:
```bash
LOCAL_NEXUS_OPEN_BROWSER=false
```

### Change Port

Set in `.env`:
```bash
LOCAL_NEXUS_PORT=8080
```

Then start with:
```bash
npm run dev
```

### Disable Hot Reload

Set in `.env`:
```bash
LOCAL_NEXUS_RELOAD=false
```

---

## Success Indicators

When everything works correctly, you'll see:

```
✓ Database directory ready: /path/to/data
✓ Database URL: sqlite:///path/to/data/local_nexus.db
✓ Database tables created/verified
INFO:     Will watch for changes in these directories: ['/path/to/local_nexus_controller']
INFO:     Uvicorn running on http://0.0.0.0:5010 (Press CTRL+C to quit)
INFO:     Started reloader process [PID] using WatchFiles
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

Then visit: **http://localhost:5010**

---

## Getting Help

If you continue to experience issues:

1. Check `TROUBLESHOOTING.md` for detailed debugging steps
2. Run the system test: `python3 test_system.py`
3. Check the error logs in `data/logs/`

For manual control, see:
- `ERROR_FIXES.md` - List of all fixes applied
- `AUDIT_REPORT.md` - Security and error handling audit
- `QUICKSTART.md` - Quick reference guide
