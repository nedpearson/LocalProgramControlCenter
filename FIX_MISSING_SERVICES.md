# Fix Missing Service Files

## Problem
Your dashboard shows 7 services that can't start because their files/directories don't exist:

1. Forensic_CPA_AI (port 5000)
2. Pearson_Nexus_AI_NEW-main (port 3040)
3. ai-financial-advisor (port 3009)
4. pearson-nexus-ai-monorepo (port 3030)
5. prototype (port 3003)
6. rest-express (port 3012)
7. retail-commission-tracker (port 3050)

## Solution Options

### Option 1: Delete All Broken Services and Start Fresh

**Via Dashboard UI:**
1. Go to http://localhost:5010/services
2. Click on each service
3. Click "Delete" button on each service
4. Then import fresh bundles or use auto-discovery

**Via API (if you have curl):**
```bash
# Get service IDs
curl http://localhost:5010/api/services

# Delete each service by ID
curl -X DELETE http://localhost:5010/api/services/1
curl -X DELETE http://localhost:5010/api/services/2
# ... repeat for all services
```

### Option 2: Clone/Download Missing Repositories

If you have the repositories on GitHub or elsewhere:

```bash
# Create a repositories folder
mkdir -p ~/repositories

# Clone your projects
cd ~/repositories
git clone https://github.com/YOUR_USERNAME/Forensic_CPA_AI.git
git clone https://github.com/YOUR_USERNAME/Pearson_Nexus_AI_NEW-main.git
git clone https://github.com/YOUR_USERNAME/ai-financial-advisor.git
git clone https://github.com/YOUR_USERNAME/pearson-nexus-ai-monorepo.git
git clone https://github.com/YOUR_USERNAME/prototype.git
git clone https://github.com/YOUR_USERNAME/rest-express.git
git clone https://github.com/YOUR_USERNAME/retail-commission-tracker.git

# Then use auto-discovery to re-import them
# Go to: http://localhost:5010/import
# Use "Import from folder" with path: /home/user/repositories
```

### Option 3: Use GitHub Import Feature

If you have a GitHub token:

1. Go to http://localhost:5010/import
2. Click "Connect GitHub (mobile)" to authenticate
3. Click "Load my repos" to see all your repositories
4. Select each repository and import it
5. The system will clone them locally and register them

### Option 4: Import from Bundles

If you have `.json` bundle files:

1. Go to http://localhost:5010/import
2. Drag and drop the `.json` bundle files
3. Or use "Import bundle" and paste the JSON

## Recommended Approach

**For best results:**

1. **Delete all broken services** (Option 1)
2. **Connect GitHub** and use auto-import (Option 3), OR
3. **Clone repos manually** then use auto-discovery (Option 2)

## Quick Commands

```bash
# Check what directories you have
ls -la ~/repositories 2>/dev/null || echo "No repositories folder"
ls -la ~/Documents 2>/dev/null || echo "No Documents folder"
ls -la ~ | grep -i pearson
ls -la ~ | grep -i forensic

# Create a workspace for your projects
mkdir -p ~/repositories
cd ~/repositories

# After cloning/downloading projects, verify they exist
ls -la ~/repositories
```

## Need Help?

If you're not sure which option to choose, answer these questions:

1. **Do you have GitHub repos for these projects?** → Use Option 3
2. **Do you have the code on another computer?** → Copy it over, then use Option 2
3. **Do you have .json bundle files?** → Use Option 4
4. **Starting completely fresh?** → Use Option 1, then import as needed

## Next Steps

After fixing the services:

1. Verify paths are correct: http://localhost:5010/services
2. Install dependencies for each service (npm install, pip install, etc.)
3. Start services from the dashboard
4. Check for port conflicts and resolve them
