# Local Nexus Controller - Cheat Sheet

## 🚀 Quick Commands

```powershell
# Start development server (with live reload)
npm run dev

# Start production server (no reload)
npm start

# Install dependencies
npm install

# Build (verification only for Python)
npm run build
```

## 📁 Key Locations

| What | Where |
|------|-------|
| **Your programs** | `C:\Users\nedpe\Desktop\Repositories` |
| **ZIP drop zone** | `C:\Users\nedpe\Desktop` |
| **Controller code** | `C:\Users\nedpe\LocalNexusController` |
| **Database** | `data/local_nexus.db` |
| **Logs** | `data/logs/` |
| **Config** | `.env` |

## 🌐 URLs

| Service | URL |
|---------|-----|
| **Dashboard** | http://localhost:5010 |
| **API Docs** | http://localhost:5010/docs |
| **Services** | http://localhost:5010/services |
| **Import** | http://localhost:5010/import |

## ⚙️ Configuration (.env)

```bash
# Live reload (instant changes)
LOCAL_NEXUS_RELOAD=true

# Auto-discovery (scan repos folder)
LOCAL_NEXUS_AUTO_DISCOVERY_ENABLED=true
LOCAL_NEXUS_REPOSITORIES_FOLDER=C:\Users\nedpe\Desktop\Repositories

# File watcher (auto-import ZIPs)
LOCAL_NEXUS_FILE_WATCHER_ENABLED=true
LOCAL_NEXUS_FILE_WATCHER_FOLDER=C:\Users\nedpe\Desktop

# Auto-start services on boot
LOCAL_NEXUS_AUTO_START_ALL_ON_BOOT=true
```

## 🔄 Live Reload Workflow

1. **Edit** any file (Python, HTML, CSS, JS)
2. **Save** (Ctrl+S)
3. **Wait** 1-2 seconds for reload
4. **Refresh** browser (F5 or Ctrl+Shift+R)
5. **See changes** instantly!

## 📦 Adding Programs

### Method 1: Direct Copy
```powershell
# Copy program folder to repositories
cp -r "MyApp" "C:\Users\nedpe\Desktop\Repositories\"
# Restart controller to auto-discover
```

### Method 2: ZIP File
```powershell
# Drop ZIP on Desktop
# File watcher automatically extracts and imports
```

### Method 3: API Import
```powershell
# Use the Import page in dashboard
# Or POST to /api/import/bundle
```

## 🎮 Service Control

### Via Dashboard
- Click **"Launch"** button to open in browser
- Click **"Start"** to start the service
- Click **"Stop"** to stop the service
- Click **"Restart"** to restart the service

### Via API
```bash
# Start service
curl -X POST http://localhost:5010/api/services/{id}/start

# Stop service
curl -X POST http://localhost:5010/api/services/{id}/stop

# Restart service
curl -X POST http://localhost:5010/api/services/{id}/restart

# Get service details
curl http://localhost:5010/api/services/{id}
```

## 🔍 Troubleshooting

### Server Won't Start
```powershell
# Check if port is in use
netstat -ano | findstr :5010

# Check Python installed
python --version

# Reinstall dependencies
pip install -r requirements.txt
```

### Changes Not Showing
```bash
# 1. Verify reload enabled
LOCAL_NEXUS_RELOAD=true

# 2. Hard refresh browser
Ctrl + Shift + R

# 3. Check terminal for errors
# Look for syntax errors or exceptions
```

### Service Won't Start
```powershell
# Check service details in dashboard
# Verify start_command is correct
# Check working_directory exists
# Review logs in service detail page
```

## 🪟 Windows Startup

### Enable Auto-Start
```powershell
.\tools\setup_windows_startup.ps1
```

### Disable Auto-Start
```powershell
.\tools\disable_windows_startup.ps1
```

### Check Status
```powershell
Get-ScheduledTask -TaskName "LocalNexusController_AutoStart"
```

## 🗂️ File Structure

```
LocalNexusController/
├── .env                    # Your configuration
├── package.json           # npm scripts
├── requirements.txt       # Python dependencies
├── local_nexus_controller/
│   ├── __main__.py       # Entry point
│   ├── main.py           # FastAPI app
│   ├── models.py         # Database models
│   ├── settings.py       # Settings loader
│   ├── routers/          # API routes
│   ├── services/         # Business logic
│   ├── templates/        # HTML pages
│   └── static/           # CSS, JS
├── data/
│   ├── local_nexus.db    # SQLite database
│   └── logs/             # Service logs
└── tools/                # Utility scripts
```

## 📋 Common Tasks

### View All Services
```bash
curl http://localhost:5010/api/services
```

### Scan for New Programs
```bash
curl -X POST http://localhost:5010/api/autodiscovery/scan \
  -H "Content-Type: application/json" \
  -d '{"folder_path":"C:\\Users\\nedpe\\Desktop\\Repositories","auto_import":true}'
```

### Get Summary
```bash
curl http://localhost:5010/api/summary
```

### List Ports
```bash
curl http://localhost:5010/api/ports
```

## 🎨 Customization

### Change Port
```bash
# In .env
LOCAL_NEXUS_PORT=8080
```

### Change Theme Colors
```css
/* Edit local_nexus_controller/static/styles.css */
/* Uses Tailwind CSS classes */
```

### Add New Page
1. Create template in `templates/`
2. Add route in `routers/ui.py`
3. Add nav link in `templates/base.html`

## 📚 Documentation

| Guide | Purpose |
|-------|---------|
| **README.md** | Overview and features |
| **LIVE_RELOAD.md** | Live reload guide |
| **DEVELOPMENT.md** | Development practices |
| **RECOMMENDATIONS.md** | Best practices and tips |
| **QUICKSTART.md** | 5-minute setup |
| **CHEAT_SHEET.md** | This file! |

## 💡 Pro Tips

1. **Keep Terminal Visible** - Watch reload status and errors
2. **Use Hard Refresh** - Ctrl+Shift+R ensures CSS updates
3. **Test Incrementally** - Small changes are easier to debug
4. **Check Logs** - Service detail page shows recent logs
5. **Use API Docs** - Visit `/docs` for interactive API testing
6. **Backup Database** - Copy `data/local_nexus.db` regularly
7. **Version Control** - Git everything except `.env` and `data/`

## 🆘 Getting Help

1. Check this cheat sheet
2. Read the relevant guide (see Documentation above)
3. Check API docs at `/docs`
4. Review terminal output for errors
5. Query database directly: `sqlite3 data/local_nexus.db`

## 🎯 Next Steps

- [ ] Configure auto-discovery with your repos folder
- [ ] Enable file watcher for ZIP imports
- [ ] Set up Windows auto-start
- [ ] Import your existing projects
- [ ] Enable live reload for development
- [ ] Add launch links to all services
- [ ] Test the auto-start feature
- [ ] Backup your database

---

**Quick Help:**
- **Dashboard**: http://localhost:5010
- **API Docs**: http://localhost:5010/docs
- **Live Reload**: `LOCAL_NEXUS_RELOAD=true` + `npm run dev`
- **Add Program**: Drop folder in `Repositories` or ZIP on Desktop

Happy coding! 🚀
