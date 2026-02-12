# Development Guide

## Live Reload / Hot Reload

The Local Nexus Controller now supports **live reloading** for rapid development and testing.

### What Gets Reloaded

When you make changes to any of these file types, the server automatically restarts:

- **Python files** (`.py`) - Backend logic, models, routes
- **HTML templates** (`.html`) - Jinja2 templates in `templates/`
- **CSS stylesheets** (`.css`) - Styles in `static/`
- **JavaScript files** (`.js`) - Frontend scripts in `static/`

### How to Enable

**1. Set in `.env` file:**
```bash
LOCAL_NEXUS_RELOAD=true
```

**2. Start the development server:**
```powershell
# Using npm
npm run dev

# OR using Python directly
python -m local_nexus_controller
```

The server will now watch for file changes and automatically reload when you save.

### Development Workflow

**In Bolt.new:**
1. Make changes to any file
2. Save the file (Ctrl+S or Cmd+S)
3. The server automatically detects the change
4. Server restarts in ~1-2 seconds
5. Refresh your browser to see changes

**In Cursor:**
1. Edit files in your local folder
2. Save changes
3. Server auto-reloads
4. Refresh browser to see updates

### Tips for Faster Development

1. **Keep browser tab open**: Just refresh after making changes
2. **Use browser dev tools**: Press F12 to inspect and debug
3. **Check terminal output**: Server logs show reload status
4. **Make incremental changes**: Test small changes before making large ones
5. **Disable auto-start features**: Turn off `AUTO_START_ALL_ON_BOOT` during development

### What Happens During Reload

When a file changes:
1. Uvicorn detects the file modification
2. Current server process stops gracefully
3. New server process starts with updated code
4. Database connections are re-established
5. Routes and templates are reloaded
6. Server is ready in 1-2 seconds

### Troubleshooting

**Server not reloading:**
- Verify `LOCAL_NEXUS_RELOAD=true` in `.env`
- Check terminal for error messages
- Make sure you're running `npm run dev` (not `npm start`)
- Restart the server manually if needed

**Changes not visible in browser:**
- Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
- Clear browser cache
- Check browser console for errors (F12)
- Verify file was saved correctly

**Server crashes on reload:**
- Check syntax errors in Python files
- Verify template syntax in HTML files
- Review terminal output for error details
- Fix the error and save again

## Development Best Practices

### Project Structure

```
local_nexus_controller/
├── main.py              # FastAPI app setup
├── models.py            # SQLModel database models
├── settings.py          # Configuration management
├── db.py                # Database initialization
├── routers/             # API route handlers
│   ├── api_services.py
│   ├── api_databases.py
│   └── ui.py           # Web page routes
├── services/            # Business logic
│   ├── process_manager.py
│   ├── auto_discovery.py
│   └── file_watcher.py
├── templates/           # Jinja2 HTML templates
│   ├── base.html
│   ├── dashboard.html
│   └── services.html
└── static/              # CSS, JS, images
    ├── styles.css
    └── app.js
```

### Making Changes

**Adding a new route:**
1. Create or edit file in `routers/`
2. Define route handler function
3. Include router in `main.py`
4. Test with browser or API client

**Modifying templates:**
1. Edit HTML file in `templates/`
2. Use Jinja2 syntax: `{{ variable }}`, `{% block %}`
3. Save and refresh browser
4. Check for template errors in terminal

**Updating styles:**
1. Edit `static/styles.css`
2. Save changes
3. Hard refresh browser (Ctrl+Shift+R)
4. Use browser dev tools to debug

**Adding JavaScript:**
1. Edit `static/app.js`
2. Add functions or event listeners
3. Save and refresh browser
4. Test in browser console

### Database Changes

**Modifying models:**
1. Edit `models.py`
2. Add/modify SQLModel classes
3. Update `db._sqlite_migrate()` if needed
4. Restart server (auto-reload handles this)
5. Test with database queries

**Note**: SQLite schema changes require migration logic in `db._sqlite_migrate()`

### Testing Changes

**Manual testing:**
```powershell
# Start development server
npm run dev

# In another terminal, test API endpoints
curl http://localhost:5010/api/services

# Or use the Swagger docs
# Open: http://localhost:5010/docs
```

**Testing process management:**
```powershell
# Test service start/stop
curl -X POST http://localhost:5010/api/services/{id}/start
curl -X POST http://localhost:5010/api/services/{id}/stop
```

### Debugging

**Python debugging:**
- Add `print()` statements
- Check terminal output
- Use Python debugger: `import pdb; pdb.set_trace()`

**Frontend debugging:**
- Open browser DevTools (F12)
- Check Console tab for JavaScript errors
- Use Network tab to inspect API calls
- Use Elements tab to debug HTML/CSS

**Database debugging:**
- Query SQLite directly: `sqlite3 data/local_nexus.db`
- Check database file exists: `ls data/local_nexus.db`
- View schema: `.schema` in sqlite3

## Common Development Tasks

### Add a new API endpoint

1. Create route in appropriate router file
2. Define request/response models with Pydantic
3. Implement handler function
4. Test with Swagger docs at `/docs`

### Add a new page to dashboard

1. Create HTML template in `templates/`
2. Extend `base.html` template
3. Add route in `routers/ui.py`
4. Add navigation link in `base.html`
5. Style with Tailwind CSS classes

### Add a new service feature

1. Update `models.py` with new fields
2. Add migration in `db._sqlite_migrate()`
3. Update API endpoints in routers
4. Update templates to display new data
5. Test end-to-end

## Performance Tips

- **Minimize auto-discovery scope**: Only scan necessary folders
- **Disable features during dev**: Turn off file watcher if not needed
- **Use SQLite WAL mode**: Better concurrent access
- **Keep logs small**: Rotate logs regularly
- **Profile slow endpoints**: Use timing decorators

## Git Workflow

```bash
# Start feature branch
git checkout -b feature/my-feature

# Make changes with live reload
# Test thoroughly

# Commit changes
git add .
git commit -m "Add my feature"

# Push to remote
git push origin feature/my-feature
```

## Production Deployment

When deploying to production:

1. **Disable reload**: Set `LOCAL_NEXUS_RELOAD=false`
2. **Use production host**: Set `LOCAL_NEXUS_HOST=127.0.0.1`
3. **Set secure token**: Generate strong `LOCAL_NEXUS_TOKEN`
4. **Configure firewall**: Restrict access to port 5010
5. **Enable startup**: Use `setup_windows_startup.ps1`

## Getting Help

- **Documentation**: Check `README.md` and this file
- **API docs**: Visit `/docs` when server is running
- **Logs**: Check terminal output for errors
- **Database**: Query SQLite file directly
- **Community**: Search GitHub issues or create new one

## Next Steps

- Read `RECOMMENDATIONS.md` for best practices
- Review `README.md` for feature overview
- Check `QUICKSTART.md` for setup guide
- Explore API at `/docs` endpoint

Happy developing!
