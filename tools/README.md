# Tools Directory

This folder contains utility scripts for managing the Local Nexus Controller.

---

## 🚀 Auto-Start Scripts (Recommended)

### Enable Auto-Start on Windows Boot

**`ENABLE_AUTO_START.bat`** ⭐
- Double-click to enable automatic startup
- Requires administrator access
- Configures Windows Task Scheduler
- Controller starts automatically when you log in

**`DISABLE_AUTO_START.bat`**
- Double-click to disable automatic startup
- Requires administrator access
- Removes Task Scheduler task

📖 Full guide: [AUTO_START_GUIDE.md](../AUTO_START_GUIDE.md)

---

## 🔧 PowerShell Scripts

### Auto-Start Management

**`setup_auto_start.ps1`**
- Sets up Windows Task Scheduler for auto-start
- Creates startup batch file automatically
- Runs at user logon
- Requires admin privileges

**`disable_auto_start.ps1`**
- Removes auto-start configuration
- Deletes Task Scheduler task
- Requires admin privileges

### Desktop Widget (Alternative Auto-Start)

**`enable_startup.ps1`**
- Creates a desktop widget that launches on boot
- Opens dashboard in a small window (bottom-left corner)
- Uses Edge/Chrome/Brave browser in app mode

**`disable_startup.ps1`**
- Removes desktop widget auto-start

**`start_dashboard_widget.ps1`**
- Manually launch the dashboard widget
- Customize window size/position in this file

---

## 📦 Import & Validation Tools

**`import_bundle.py`**
- Import service/database bundles into the controller
- Usage: `python tools/import_bundle.py path/to/bundle.json`
- Validates JSON before importing

**`validate_bundle.py`**
- Validate bundle JSON format
- Normalizes Windows paths
- Usage: `python tools/validate_bundle.py path/to/bundle.json`

---

## 🔍 Verification Tools

**`verify_remotes.py`**
- Check Git remote URLs for registered services
- Ensures remotes are properly configured
- Usage: `python tools/verify_remotes.py`

---

## 📁 Auto-Generated Files

These files are created automatically by the setup scripts:

**`start_nexus_on_boot.bat`**
- Created by `setup_auto_start.ps1`
- Used by Task Scheduler
- Changes to project directory and runs `npm run dev`

**`start_on_boot.vbs`**
- VBScript launcher (alternative method)
- Runs silently in background
- Can be used with Startup folder

---

## Quick Reference

| What do you want to do? | Use this file |
|-------------------------|---------------|
| Enable auto-start (easiest) | `ENABLE_AUTO_START.bat` |
| Disable auto-start | `DISABLE_AUTO_START.bat` |
| Enable desktop widget | `enable_startup.ps1` |
| Disable desktop widget | `disable_startup.ps1` |
| Import a bundle | `import_bundle.py` |
| Validate a bundle | `validate_bundle.py` |
| Check Git remotes | `verify_remotes.py` |

---

## Usage Examples

### Enable Auto-Start
```cmd
REM Method 1: Double-click the file
ENABLE_AUTO_START.bat

REM Method 2: PowerShell
.\tools\setup_auto_start.ps1
```

### Import a Bundle
```powershell
python .\tools\import_bundle.py .\sample_data\import_bundle.json
```

### Validate a Bundle
```powershell
python .\tools\validate_bundle.py C:\MyProject\local-nexus.bundle.json
```

### Launch Desktop Widget Manually
```powershell
.\tools\start_dashboard_widget.ps1
```

---

## Troubleshooting

### "Access Denied" Error
- Right-click the .bat or .ps1 file
- Select "Run as administrator"

### "Scripts are disabled" Error
Run in PowerShell as admin:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Auto-Start Not Working
1. Open Task Scheduler (`taskschd.msc`)
2. Look for "Local Nexus Controller"
3. Check task status and history
4. See [AUTO_START_GUIDE.md](../AUTO_START_GUIDE.md) for detailed troubleshooting

---

## For Developers

All tools follow these conventions:

- **Batch files (.bat)**: Simple launchers for Windows users
- **PowerShell scripts (.ps1)**: Main implementation logic
- **Python scripts (.py)**: Data validation and import logic
- **VBScript files (.vbs)**: Silent background launchers

The auto-start system uses Windows Task Scheduler for reliability.

---

## Related Documentation

- [AUTO_START_GUIDE.md](../AUTO_START_GUIDE.md) - Complete auto-start guide
- [WINDOWS_SETUP.md](../WINDOWS_SETUP.md) - Windows troubleshooting
- [README.md](../README.md) - Main project documentation
