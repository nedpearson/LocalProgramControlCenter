# Forensic CPA AI - Deployment Guide

This guide explains how to deploy the Forensic CPA AI application to its target location and integrate it with the Local Nexus Controller.

## Current Status

The application files are currently located in:
- `LocalProgramControlCenter/forensic_cpa_ai/`

They need to be deployed to:
- `C:\Users\nedpe\Desktop\Repositories\Forensic_CPA_AI\`

## Deployment Methods

### Method 1: Automatic Deployment (Windows)

1. Navigate to the forensic_cpa_ai directory:
   ```cmd
   cd LocalProgramControlCenter\forensic_cpa_ai
   ```

2. Run the deployment script:
   ```cmd
   DEPLOY.bat
   ```

This will:
- Create the target directory if it doesn't exist
- Copy all necessary files
- Display next steps

### Method 2: Manual Deployment

1. Create the target directory:
   ```cmd
   mkdir C:\Users\nedpe\Desktop\Repositories\Forensic_CPA_AI
   ```

2. Copy all files from `forensic_cpa_ai/` to the target directory:
   - main.py
   - requirements.txt
   - README.md
   - SETUP_INSTRUCTIONS.md
   - .env.example
   - .gitignore
   - local-nexus.bundle.json
   - QUICK_START.bat
   - DEPLOY.bat (optional)

### Method 3: Git Clone (If Repository Exists)

If this project has been pushed to Git:

```cmd
cd C:\Users\nedpe\Desktop\Repositories
git clone <repository-url> Forensic_CPA_AI
cd Forensic_CPA_AI
```

## Post-Deployment Setup

After deploying the files:

### 1. Navigate to the Deployed Location

```cmd
cd C:\Users\nedpe\Desktop\Repositories\Forensic_CPA_AI
```

### 2. Quick Start (Recommended)

Simply run:
```cmd
QUICK_START.bat
```

This will automatically:
- Check for Python installation
- Create virtual environment
- Install dependencies
- Create .env file
- Start the application

### 3. Manual Setup (Alternative)

If you prefer manual setup:

```cmd
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
copy .env.example .env

# Start application
python main.py
```

## Integration with Local Nexus Controller

Once the application is deployed and running:

### Step 1: Verify the Application is Running

```cmd
# From the Forensic_CPA_AI directory
python main.py
```

You should see:
```
╔══════════════════════════════════════════════════════════════╗
║          Forensic CPA AI - Document Processing System        ║
╚══════════════════════════════════════════════════════════════╝

🚀 Server starting on http://localhost:5000
```

### Step 2: Register with Local Nexus Controller

#### Option A: Dashboard Import

1. Open Local Nexus Controller: http://127.0.0.1:5010
2. Navigate to **Import** section
3. Open `local-nexus.bundle.json` in a text editor
4. Copy the entire contents
5. Paste into the Import field
6. Click **Import**

#### Option B: Command Line Import

From the Local Nexus Controller directory:

```cmd
cd C:\Users\nedpe\LocalNexusController
python .\tools\import_bundle.py C:\Users\nedpe\Desktop\Repositories\Forensic_CPA_AI\local-nexus.bundle.json
```

#### Option C: Auto-Discovery

If auto-discovery is enabled in Local Nexus Controller, it should automatically detect the project in the Repositories folder.

### Step 3: Verify Registration

1. Open Local Nexus Controller dashboard
2. Look for "Forensic CPA AI" in the services list
3. Check that the status shows as running
4. Test the health check endpoint

## Configuration

### Port Configuration

Default port: 5000

To change the port, edit `.env`:
```env
PORT=5001
```

Or set environment variable:
```cmd
set PORT=5001
python main.py
```

### Debug Mode

To enable Flask debug mode, edit `.env`:
```env
FLASK_DEBUG=true
```

## Verification Steps

After deployment and setup:

1. ✅ **Application starts without errors**
   - Run: `python main.py`
   - No import errors or missing dependencies

2. ✅ **Health check responds**
   - Visit: http://localhost:5000/health
   - Should return: `{"status": "healthy", ...}`

3. ✅ **API information displays**
   - Visit: http://localhost:5000/
   - Should show API endpoints and information

4. ✅ **Registered in Local Nexus Controller**
   - Check dashboard at http://127.0.0.1:5010
   - "Forensic CPA AI" appears in services list

5. ✅ **File upload works**
   - Test uploading a PDF, Excel, or Word document
   - Check that processing completes successfully

## Troubleshooting

### Issue: Python Not Found

**Solution:**
1. Install Python from Microsoft Store or python.org
2. Ensure "Add Python to PATH" is checked during installation
3. Restart Command Prompt after installation

### Issue: Port 5000 Already in Use

**Solution:**
```cmd
# Option 1: Use different port
set PORT=5001
python main.py

# Option 2: Find and stop the process using port 5000
netstat -ano | findstr :5000
taskkill /PID <process_id> /F
```

### Issue: Virtual Environment Activation Fails

**Solution for PowerShell:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then rerun:
```powershell
.venv\Scripts\Activate.ps1
```

### Issue: Dependencies Installation Fails

**Solution:**
```cmd
# Upgrade pip first
python -m pip install --upgrade pip

# Then reinstall dependencies
pip install -r requirements.txt
```

### Issue: Application Not Accessible from Local Nexus Controller

**Solution:**
1. Verify the application is running: http://localhost:5000/health
2. Check that working_directory in local-nexus.bundle.json matches actual location
3. Verify port configuration matches (default: 5000)
4. Re-import the bundle after fixing any path issues

## Directory Structure After Deployment

```
C:\Users\nedpe\Desktop\Repositories\Forensic_CPA_AI\
├── main.py                      # Main Flask application
├── requirements.txt             # Python dependencies
├── README.md                    # Main documentation
├── SETUP_INSTRUCTIONS.md        # Setup guide
├── DEPLOYMENT_GUIDE.md          # This file
├── .env.example                 # Environment template
├── .env                         # Environment config (created on setup)
├── .gitignore                   # Git ignore patterns
├── local-nexus.bundle.json      # LNC import bundle
├── QUICK_START.bat              # Quick start script
├── DEPLOY.bat                   # Deployment script
├── .venv/                       # Virtual environment (created on setup)
└── uploads/                     # Uploaded files (created on first run)
```

## Next Steps After Successful Deployment

1. 🔄 **Test document processing**
   - Upload sample PDF, Excel, and Word files
   - Verify extraction works correctly

2. 🔄 **Configure auto-start** (optional)
   - Set up with Local Nexus Controller auto-start
   - Application starts automatically with controller

3. 🔄 **Customize settings**
   - Adjust port if needed
   - Configure upload size limits
   - Enable/disable debug mode

4. 🔄 **Add to Git** (optional)
   - Initialize Git repository
   - Add remote
   - Commit initial version

## Support

For deployment issues:

1. Check the error messages in the terminal
2. Verify all files were copied correctly
3. Ensure Python 3.8+ is installed
4. Review the SETUP_INSTRUCTIONS.md file
5. Check Local Nexus Controller logs at `data/logs/`

## Security Notes

- Application runs on localhost only (0.0.0.0 binding for containers)
- Maximum 16MB file upload size
- Only specific file types allowed
- File names are sanitized
- No authentication by default (add if exposing to network)

## Production Considerations

For production deployment:

- [ ] Add authentication/authorization
- [ ] Configure HTTPS
- [ ] Set up proper logging
- [ ] Add rate limiting
- [ ] Configure backup for uploads/
- [ ] Set up monitoring
- [ ] Use production WSGI server (gunicorn, waitress)
- [ ] Configure proper database storage
- [ ] Add input validation and sanitization
- [ ] Set up automated testing
