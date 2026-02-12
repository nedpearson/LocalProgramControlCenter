# Auto-Start Troubleshooting Guide

## Current Status

Your `.env` file shows:
```
LOCAL_NEXUS_AUTO_START_ALL_ON_BOOT=true
```

This means **all services with a `start_command` will automatically start** when the controller starts.

---

## How Auto-Start Works

When you start the controller (via `npm run dev` or `start.bat`):

1. Controller starts up
2. Scans database for all services
3. For each service that has a `start_command` and isn't already running:
   - Executes the start command
   - Logs output to `data/logs/`
   - Tracks the process PID
   - Updates service status

---

## Verifying Auto-Start Is Working

### Step 1: Start the Controller

```cmd
start.bat
```

Or double-click `start.bat`.

### Step 2: Check the Dashboard

Open http://localhost:5010

Look at the Services page - you should see:
- Services with **green "Running"** status = Started successfully
- Services with **red "Error"** status = Failed to start
- Services with **gray "Stopped"** status = No start command or not auto-started

### Step 3: Check Service Logs

For any service with errors:
1. Click on the service name
2. Scroll down to "Logs" section
3. Read the error message

Common errors:
- **Missing dependencies** - Need to install packages first
- **Port already in use** - Another program using the port
- **Wrong working directory** - Path doesn't exist
- **Command not found** - Missing Python, Node, etc.

---

## Common Issues & Solutions

### Issue 1: Service Shows "Error" Status

**Cause:** Start command failed

**Solution:**
1. Click the service name in dashboard
2. Check the "Last Error" field
3. Check logs (scroll down to Logs section)
4. Fix the issue (see specific errors below)

### Issue 2: "Port Already in Use"

**Cause:** Another program is using the port

**Solution:**
The controller auto-heals this! It will:
1. Detect the port conflict
2. Assign a new available port
3. Update the service URLs
4. Try starting again

If it still fails, manually change the port:
1. Go to Services page
2. Click service name
3. Change "Port" field
4. Click "Update Service"
5. Click "Start" button

### Issue 3: "Command Not Found"

**Cause:** Missing Python, Node, or other runtime

**Solution:**

For Python services:
```cmd
python --version
```
If error: Install Python from https://python.org

For Node services:
```cmd
node --version
npm --version
```
If error: Install Node.js from https://nodejs.org

### Issue 4: "ModuleNotFoundError" or Missing Dependencies

**Cause:** Service dependencies not installed

**Solution:**

For Python services:
```cmd
cd C:\path\to\service
pip install -r requirements.txt
```

For Node services:
```cmd
cd C:\path\to\service
npm install
```

Then restart the service from dashboard.

### Issue 5: "Working Directory Does Not Exist"

**Cause:** Service working_directory path is wrong

**Solution:**
1. Find the actual service folder location
2. Go to Services page → Click service name
3. Update "Working Directory" field with correct path
4. Click "Update Service"
5. Click "Start" button

Example paths:
- `C:\Users\nedpe\Desktop\Repositories\my-service`
- `C:\Users\nedpe\Projects\my-api`

### Issue 6: Service Starts Then Immediately Stops

**Cause:** Service crashes right after starting

**Solution:**
1. Click service name
2. Scroll to Logs section
3. Read the crash error
4. Fix the root cause (usually missing config or dependencies)

---

## Checking Service Logs

### Via Dashboard

1. Go to http://localhost:5010
2. Click "Services" in navigation
3. Click the service name
4. Scroll down to "Logs" section

### Via File System

Logs are saved in:
```
data/logs/
```

Each service has its own log file:
```
data/logs/ServiceName-abc123.log
```

Open in any text editor to see detailed output.

---

## Testing Auto-Start

### Test 1: Restart Controller

1. Close the controller (Ctrl+C in terminal or close window)
2. Start again: `start.bat`
3. Check dashboard - services should auto-start

### Test 2: Add a Test Service

Create a simple test service to verify auto-start works:

1. Go to http://localhost:5010
2. Click "Services" → "New Service"
3. Fill in:
   - **Name:** Test Service
   - **Start Command:** `python -m http.server 8888`
   - **Working Directory:** `C:\Users\nedpe`
   - **Port:** 8888
4. Click "Create Service"
5. Restart controller
6. Check if Test Service auto-started

### Test 3: Check Process Manager

Windows Task Manager should show processes for running services:
1. Press Ctrl+Shift+Esc
2. Look for `python.exe`, `node.exe`, etc.
3. Should match your running services

---

## Manual Starting vs Auto-Start

### Auto-Start (Automatic on Controller Boot)

**When it runs:**
- Every time you start the controller

**What it starts:**
- All services with `start_command` defined
- Only services currently stopped
- Skips services already running

**Configuration:**
```env
LOCAL_NEXUS_AUTO_START_ALL_ON_BOOT=true
```

### Manual Start (Via Dashboard)

**When it runs:**
- Only when you click "Start" button

**What it starts:**
- Only the specific service you clicked

**Use this for:**
- Testing a service
- Restarting after making changes
- Starting services you don't want auto-started

---

## Disabling Auto-Start for Specific Services

If you want **some** services to NOT auto-start:

### Option 1: Remove Start Command Temporarily
1. Go to service detail page
2. Clear the "Start Command" field
3. Save
4. Service won't auto-start anymore

### Option 2: Disable Global Auto-Start

Edit `.env`:
```env
LOCAL_NEXUS_AUTO_START_ALL_ON_BOOT=false
```

Then manually start only the services you want via dashboard.

---

## Best Practices

### 1. Set Working Directory

Always set the working directory for each service:
```
C:\path\to\service\folder
```

Don't leave it blank unless the command uses absolute paths.

### 2. Use Correct Start Commands

**Python services:**
```
python app.py
python -m uvicorn main:app --port {PORT}
python manage.py runserver 0.0.0.0:{PORT}
```

**Node services:**
```
npm start
node server.js
npm run dev
```

**Java services:**
```
java -jar application.jar --server.port={PORT}
```

### 3. Test Before Enabling Auto-Start

1. Create the service
2. Manually start it via dashboard
3. Check if it works
4. Check logs for errors
5. Fix any issues
6. THEN enable auto-start

### 4. Use {PORT} Placeholder

If your service needs a port, use the `{PORT}` placeholder:
```
python app.py --port {PORT}
npm start -- --port {PORT}
```

The controller will replace `{PORT}` with the actual port number.

### 5. Check Logs Regularly

Look at service logs to catch issues early:
```
data/logs/
```

Or use the dashboard Logs section.

---

## Environment Variables

Services can use these environment variables automatically:

- `PORT` - Set to the service's assigned port
- `HOST` - Always set to `127.0.0.1`

Example Python code:
```python
import os
port = int(os.getenv("PORT", 3000))
host = os.getenv("HOST", "127.0.0.1")
```

Example Node code:
```javascript
const port = process.env.PORT || 3000;
const host = process.env.HOST || '127.0.0.1';
```

---

## Advanced: Custom Environment Variables

If your service needs custom env vars:

1. Go to service detail page
2. Find "Environment Overrides" section
3. Add key-value pairs:
   ```json
   {
     "DATABASE_URL": "sqlite:///data/mydb.db",
     "API_KEY_ENV": "MY_API_KEY",
     "DEBUG": "true"
   }
   ```
4. Save
5. Service will use these env vars when starting

---

## Troubleshooting Checklist

When auto-start isn't working:

- [ ] Auto-start enabled in `.env`? (`LOCAL_NEXUS_AUTO_START_ALL_ON_BOOT=true`)
- [ ] Service has `start_command` defined?
- [ ] Working directory path is correct?
- [ ] Dependencies installed? (requirements.txt, package.json)
- [ ] Port is available? (not used by another program)
- [ ] Runtime installed? (Python, Node, Java, etc.)
- [ ] Checked service logs for errors?
- [ ] Tried manual start first?

---

## Getting Help

If you're still having issues:

1. **Check the logs:**
   ```
   data/logs/
   ```

2. **Check service status:**
   Dashboard → Services → Click service name

3. **Check last error:**
   Service detail page shows "Last Error" field

4. **Test command manually:**
   ```cmd
   cd C:\path\to\service
   python app.py
   ```

   If it works manually, it should work via controller.

5. **Verify paths:**
   Make sure all paths in service config are correct and exist.

---

## Quick Reference

| Task | How To Do It |
|------|--------------|
| Enable auto-start | Set `LOCAL_NEXUS_AUTO_START_ALL_ON_BOOT=true` in `.env` |
| Disable auto-start | Set `LOCAL_NEXUS_AUTO_START_ALL_ON_BOOT=false` in `.env` |
| Check service status | Dashboard → Services |
| View service logs | Dashboard → Services → Click service → Logs section |
| Manual start | Dashboard → Services → Click service → Start button |
| Stop service | Dashboard → Services → Click service → Stop button |
| Restart service | Dashboard → Services → Click service → Restart button |
| Check log files | Open `data/logs/*.log` files |

---

## Summary

Auto-start is **already enabled** in your setup. When the controller starts:

1. ✅ Scans all services
2. ✅ Starts services with `start_command`
3. ✅ Logs output to `data/logs/`
4. ✅ Shows status in dashboard

If services aren't starting:
- Check service logs for errors
- Verify start commands are correct
- Ensure dependencies are installed
- Make sure working directories exist

**Test it now:**
1. Restart the controller
2. Open dashboard
3. Check Services page
4. Look for green "Running" statuses
5. Check logs if any errors
