# Quick Start Guide

Get your Local Nexus Controller up and running in minutes!

## Prerequisites

- Windows 10 or later
- Python 3.10 or later
- PowerShell

## Step 1: Install Dependencies

```powershell
pip install -r requirements.txt
```

## Step 2: Configure Settings

1. Copy `.env.example` to `.env`:
   ```powershell
   copy .env.example .env
   ```

2. Edit `.env` and set your paths:
   ```bash
   LOCAL_NEXUS_REPOSITORIES_FOLDER=C:\Users\nedpe\Desktop\Repositories
   LOCAL_NEXUS_FILE_WATCHER_FOLDER=C:\Users\nedpe\Desktop
   LOCAL_NEXUS_AUTO_DISCOVERY_ENABLED=true
   LOCAL_NEXUS_FILE_WATCHER_ENABLED=true
   LOCAL_NEXUS_AUTO_START_ALL_ON_BOOT=true
   ```

## Step 3: Start the Controller

```powershell
.\run.ps1
```

The dashboard will automatically open at http://localhost:5010

## Step 4: Add Programs

### Option A: Auto-Discovery (Recommended)
1. Place your program folders in `C:\Users\nedpe\Desktop\Repositories`
2. Restart the controller
3. Programs are automatically registered!

### Option B: ZIP Import
1. Drop a ZIP file containing your program onto your Desktop
2. The file watcher automatically extracts and registers it
3. Done!

### Option C: Manual Import
1. Go to http://localhost:5010/import
2. Paste an import bundle JSON
3. Click "Import"

## Step 5: Launch Programs

1. Go to the Services page
2. Click the blue "Launch" button next to any service
3. Use Start/Stop/Restart buttons to control services

## Step 6: Enable Auto-Start (Optional)

To start the controller and all services automatically on Windows startup:

```powershell
.\tools\setup_windows_startup.ps1
```

## What's Next?

- Read [RECOMMENDATIONS.md](RECOMMENDATIONS.md) for best practices
- Check the API documentation at http://localhost:5010/docs
- Explore the dashboard features
- Import your existing projects

## Common Tasks

### View All Services
```
http://localhost:5010/services
```

### View Ports
```
http://localhost:5010/ports
```

### View Databases
```
http://localhost:5010/databases
```

### View API Keys
```
http://localhost:5010/keys
```

### API Documentation
```
http://localhost:5010/docs
```

## Troubleshooting

**Controller won't start?**
- Check Python is installed: `python --version`
- Check port 5010 is available
- Review error messages in terminal

**Auto-discovery not working?**
- Verify repository folder path in `.env`
- Check folder contains valid projects
- Enable auto-discovery: `LOCAL_NEXUS_AUTO_DISCOVERY_ENABLED=true`

**Service won't start?**
- Check the service detail page for errors
- Verify start_command is correct
- Check port is available

## Help & Support

- Full documentation: [README.md](README.md)
- Recommendations: [RECOMMENDATIONS.md](RECOMMENDATIONS.md)
- API docs: http://localhost:5010/docs

Enjoy your organized development environment!
