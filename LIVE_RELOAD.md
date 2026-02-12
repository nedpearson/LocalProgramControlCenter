# Live Reload Quick Guide

## ✨ What is Live Reload?

Live reload automatically restarts your server when you save changes to files. No more manual restarts!

## 🚀 Quick Start

**Your controller is already configured for live reload!**

Just run:
```powershell
npm run dev
```

That's it! The server will now automatically reload when you make changes.

## 📝 How It Works

### In Bolt.new
1. **Edit any file** in the web interface
2. **Save** (Ctrl+S or click Save)
3. **Server auto-reloads** (watch terminal for confirmation)
4. **Refresh browser** to see changes

### In Cursor (or any editor)
1. **Open** `C:\Users\nedpe\LocalNexusController`
2. **Edit files** (Python, HTML, CSS, JS)
3. **Save** (Ctrl+S)
4. **Server auto-reloads** automatically
5. **Refresh browser** to see changes

## 📂 Files That Trigger Reload

| File Type | Location | Example |
|-----------|----------|---------|
| Python | `local_nexus_controller/*.py` | `models.py`, `main.py` |
| Templates | `local_nexus_controller/templates/*.html` | `dashboard.html` |
| Styles | `local_nexus_controller/static/*.css` | `styles.css` |
| Scripts | `local_nexus_controller/static/*.js` | `app.js` |

## 💡 Example Workflow

**Scenario**: Change the dashboard title color

1. **Open** `local_nexus_controller/templates/dashboard.html`
2. **Find** the title: `<h1 class="text-2xl">Dashboard</h1>`
3. **Change** to: `<h1 class="text-2xl text-blue-400">Dashboard</h1>`
4. **Save** the file
5. **Watch terminal**: You'll see "Reloading..."
6. **Refresh browser**: Title is now blue!

## ⚡ Speed Tips

**Faster Testing:**
- Keep browser DevTools open (F12)
- Use keyboard shortcut: Ctrl+Shift+R for hard refresh
- Edit in one window, view in another

**Reduce Reload Time:**
- Make small, focused changes
- Test one feature at a time
- Keep the terminal visible to monitor reload status

**Avoid Common Issues:**
- Wait for reload to complete before refreshing browser
- Fix syntax errors immediately (server won't start with errors)
- Hard refresh if CSS changes don't appear

## 🔧 Configuration

Live reload is controlled by `.env`:

```bash
# Enable live reload (already set!)
LOCAL_NEXUS_RELOAD=true
```

**To disable** (for production):
```bash
LOCAL_NEXUS_RELOAD=false
```

## 📊 What You'll See

**Terminal output during reload:**
```
INFO:     Uvicorn running on http://0.0.0.0:5010 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.

# After you save a file:
INFO:     WatchFiles detected changes in 'templates/dashboard.html'
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [12346]
INFO:     Started server process [12347]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## 🐛 Troubleshooting

### Changes Not Appearing?

**1. Check reload is enabled:**
```powershell
# Look in .env file
LOCAL_NEXUS_RELOAD=true
```

**2. Hard refresh browser:**
- Windows: `Ctrl + Shift + R`
- Mac: `Cmd + Shift + R`

**3. Clear browser cache:**
- Open DevTools (F12)
- Right-click refresh button
- Select "Empty Cache and Hard Reload"

### Server Not Reloading?

**1. Verify you're using npm run dev:**
```powershell
npm run dev  # ✓ Correct (uses settings)
python -m local_nexus_controller  # ✓ Also works (uses settings)
```

**2. Check terminal for errors:**
- Syntax errors prevent reload
- Fix the error and save again

**3. Restart manually if stuck:**
- Stop server: `Ctrl + C`
- Start again: `npm run dev`

### Files Not Being Watched?

The watcher monitors:
- `local_nexus_controller/**/*.py`
- `local_nexus_controller/**/*.html`
- `local_nexus_controller/**/*.css`
- `local_nexus_controller/**/*.js`

If editing files outside these patterns, they won't trigger reload.

## 🎯 Best Practices

**DO:**
- ✅ Save files before expecting changes
- ✅ Wait for reload to complete (1-2 seconds)
- ✅ Keep terminal visible to see reload status
- ✅ Test changes incrementally
- ✅ Use hard refresh for CSS changes

**DON'T:**
- ❌ Make changes without saving
- ❌ Refresh during reload
- ❌ Edit multiple files at once when testing
- ❌ Ignore error messages in terminal
- ❌ Run multiple instances of the server

## 🚦 Development vs Production

| Setting | Development | Production |
|---------|-------------|------------|
| `LOCAL_NEXUS_RELOAD` | `true` | `false` |
| `LOCAL_NEXUS_OPEN_BROWSER` | `true` | `false` |
| `LOCAL_NEXUS_HOST` | `0.0.0.0` | `127.0.0.1` |
| Start Command | `npm run dev` | `npm start` |

## 📚 Related Files

- **Configuration**: `.env` - Live reload settings
- **Server Entry**: `local_nexus_controller/__main__.py` - Uvicorn setup
- **Dev Guide**: `DEVELOPMENT.md` - Detailed development info
- **Recommendations**: `RECOMMENDATIONS.md` - Best practices

## 🎉 You're All Set!

Live reload is enabled and ready to use. Start making changes and watch them appear instantly!

```powershell
# Start developing
npm run dev

# Make changes in Bolt.new or Cursor
# Save and see changes instantly!
```

Happy coding! 🚀
