# Forensic CPA AI - Setup Instructions

## Quick Setup for Windows

### Step 1: Navigate to Project Directory

Open Command Prompt or PowerShell and navigate to the project:

```cmd
cd C:\Users\nedpe\Desktop\Repositories\Forensic_CPA_AI
```

### Step 2: Create Virtual Environment

```cmd
python -m venv .venv
```

### Step 3: Activate Virtual Environment

For Command Prompt:
```cmd
.venv\Scripts\activate.bat
```

For PowerShell:
```powershell
.venv\Scripts\Activate.ps1
```

**Note:** If you get a PowerShell execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Step 4: Install Dependencies

```cmd
pip install -r requirements.txt
```

### Step 5: Create Environment File (Optional)

```cmd
copy .env.example .env
```

Edit `.env` if you need to change the port or other settings.

### Step 6: Run the Application

```cmd
python main.py
```

The application will start on `http://localhost:5000`

## Troubleshooting

### Python Not Found

If you get "Python was not found", install Python from:
- Microsoft Store: Search for "Python 3.12" or "Python 3.11"
- Official website: https://www.python.org/downloads/

Make sure to check "Add Python to PATH" during installation.

### Port Already in Use

If port 5000 is already in use:

```cmd
# Use a different port
set PORT=5001
python main.py
```

Or edit the `.env` file and change the PORT value.

### Virtual Environment Issues

If the virtual environment doesn't work:

1. Delete the `.venv` folder
2. Recreate it: `python -m venv .venv`
3. Activate and reinstall: `.venv\Scripts\activate && pip install -r requirements.txt`

## Integration with Local Nexus Controller

Once the application is set up, you can register it with the Local Nexus Controller:

### Method 1: Import via Dashboard

1. Open Local Nexus Controller dashboard: http://127.0.0.1:5010
2. Go to the **Import** section
3. Paste the contents of `local-nexus.bundle.json`
4. Click Import

### Method 2: Command Line Import

From the Local Nexus Controller directory:

```cmd
cd C:\Users\nedpe\LocalNexusController
python .\tools\import_bundle.py C:\Users\nedpe\Desktop\Repositories\Forensic_CPA_AI\local-nexus.bundle.json
```

### Method 3: Auto-Discovery

If you have auto-discovery enabled in Local Nexus Controller, it should automatically detect this project in your Repositories folder.

## Verifying Installation

1. Start the application: `python main.py`
2. Open a browser and go to: `http://localhost:5000`
3. You should see the API information page
4. Check health: `http://localhost:5000/health`

## Testing the API

### Test with curl (Git Bash or WSL)

```bash
# Get API info
curl http://localhost:5000/

# Health check
curl http://localhost:5000/health

# Upload a file
curl -X POST -F "file=@sample.pdf" http://localhost:5000/api/upload

# List files
curl http://localhost:5000/api/files
```

### Test with PowerShell

```powershell
# Get API info
Invoke-RestMethod http://localhost:5000/

# Health check
Invoke-RestMethod http://localhost:5000/health

# List files
Invoke-RestMethod http://localhost:5000/api/files
```

## Next Steps

After successful setup:

1. ✅ Application runs without errors
2. ✅ Health check returns "healthy"
3. ✅ API endpoints respond correctly
4. 🔄 Register with Local Nexus Controller
5. 🔄 Test document upload functionality
6. 🔄 Explore API endpoints

## Support

If you encounter issues:

1. Check that all dependencies are installed: `pip list`
2. Verify Python version: `python --version` (should be 3.8+)
3. Check the error logs in the terminal
4. Ensure no other application is using port 5000

For specific errors, refer to the README.md troubleshooting section.
