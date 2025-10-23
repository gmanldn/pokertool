# PokerTool Update Procedures

**Date**: 2025-10-23
**Purpose**: Guide for safely updating PokerTool while it's running

## Overview

The Update Manager provides a reliable way to update PokerTool without losing state or causing downtime. It handles graceful shutdown, code updates, frontend rebuilds, and restart.

## Quick Start

### Complete Update (Recommended)

```bash
# Stop app -> Update code -> Restart app (all in one)
./scripts/full_update.sh
```

### Manual Step-by-Step

```bash
# 1. Check app status
./scripts/status.sh

# 2. Gracefully stop the app
./scripts/quiesce.sh

# 3. Pull changes and rebuild
./scripts/update.sh

# 4. Restart the app
./scripts/resume.sh
```

## Detailed Commands

### 1. Quiesce (Graceful Shutdown)

**Purpose**: Safely stop the application while preserving state

```bash
./scripts/quiesce.sh
# OR
python3 scripts/update_manager.py quiesce
```

**What it does**:
- Sends SIGTERM for graceful shutdown
- Waits up to 30 seconds for clean exit
- Saves application state to `.update_state.json`
- Cleans up PID file
- Falls back to SIGKILL if necessary

**Output**:
```
[2025-10-23 15:30:00] [INFO] ============================================================
[2025-10-23 15:30:00] [INFO] QUIESCE: Initiating graceful shutdown
[2025-10-23 15:30:00] [INFO] ============================================================
[2025-10-23 15:30:00] [INFO] Sending SIGTERM to process 12345
[2025-10-23 15:30:00] [INFO] Waiting for graceful shutdown (max 30 seconds)...
[2025-10-23 15:30:05] [INFO] ✓ Application stopped gracefully
```

### 2. Update Code

**Purpose**: Pull latest changes and rebuild frontend

```bash
./scripts/update.sh
# OR
python3 scripts/update_manager.py update
```

**What it does**:
- Pulls latest changes from git
- Installs/updates npm dependencies
- Builds React frontend
- Updates Python dependencies
- Logs all operations

**Output**:
```
[2025-10-23 15:30:10] [INFO] ============================================================
[2025-10-23 15:30:10] [INFO] UPDATE: Pulling latest changes and rebuilding
[2025-10-23 15:30:10] [INFO] ============================================================
[2025-10-23 15:30:10] [INFO] Pulling latest changes from git...
[2025-10-23 15:30:12] [INFO] Already up to date.
[2025-10-23 15:30:12] [INFO] Checking for frontend changes...
[2025-10-23 15:30:12] [INFO] Installing npm dependencies...
[2025-10-23 15:30:45] [INFO] Building frontend...
[2025-10-23 15:31:20] [INFO] ✓ Frontend built successfully
[2025-10-23 15:31:20] [INFO] Updating Python dependencies...
[2025-10-23 15:31:35] [INFO] ✓ Code update completed successfully
```

### 3. Resume (Restart)

**Purpose**: Restart the application

```bash
./scripts/resume.sh
# OR
python3 scripts/update_manager.py restart
```

**What it does**:
- Starts start.py in background
- Saves PID to `.pokertool.pid`
- Waits and verifies successful start
- Reports CPU and memory usage

**Output**:
```
[2025-10-23 15:31:40] [INFO] ============================================================
[2025-10-23 15:31:40] [INFO] RESTART: Starting application
[2025-10-23 15:31:40] [INFO] ============================================================
[2025-10-23 15:31:40] [INFO] Starting /path/to/start.py...
[2025-10-23 15:31:45] [INFO] ✓ Application started successfully (PID: 12456)
[2025-10-23 15:31:48] [INFO] ✓ Application is healthy
[2025-10-23 15:31:48] [INFO]   - CPU: 2.5%
[2025-10-23 15:31:48] [INFO]   - Memory: 145.2 MB
```

### 4. Status Check

**Purpose**: Check if application is running and get health metrics

```bash
./scripts/status.sh
# OR
python3 scripts/update_manager.py status
```

**What it does**:
- Checks if process is running
- Reports PID, CPU, memory, thread count
- Shows when application started
- Displays saved state if available

**Output (Running)**:
```
[2025-10-23 15:35:00] [INFO] ============================================================
[2025-10-23 15:35:00] [INFO] STATUS: Application Status
[2025-10-23 15:35:00] [INFO] ============================================================
[2025-10-23 15:35:00] [INFO] ✓ Application is RUNNING
[2025-10-23 15:35:00] [INFO]   - PID: 12456
[2025-10-23 15:35:00] [INFO]   - CPU: 1.8%
[2025-10-23 15:35:00] [INFO]   - Memory: 148.5 MB
[2025-10-23 15:35:00] [INFO]   - Threads: 12
[2025-10-23 15:35:00] [INFO]   - Started: 2025-10-23T15:31:42
```

**Output (Stopped)**:
```
[2025-10-23 15:35:00] [INFO] ============================================================
[2025-10-23 15:35:00] [INFO] STATUS: Application Status
[2025-10-23 15:35:00] [INFO] ============================================================
[2025-10-23 15:35:00] [INFO] ✗ Application is NOT RUNNING

Saved state found:
[2025-10-23 15:35:00] [INFO]   - Shutdown time: 2025-10-23T15:30:05
[2025-10-23 15:35:00] [INFO]   - Reason: manual_quiesce
```

### 5. Full Update (One Command)

**Purpose**: Complete update cycle in one command

```bash
./scripts/full_update.sh
# OR
python3 scripts/update_manager.py full
```

**What it does**:
1. Quiesce (graceful shutdown)
2. Update code (git pull + rebuild)
3. Restart application
4. Verify successful restart

**Output**: Combined output from all three steps

## Update Workflows

### Scenario 1: Regular Code Update

When you've pulled code changes and need to apply them:

```bash
./scripts/full_update.sh
```

### Scenario 2: Frontend-Only Changes

If you only changed frontend code:

```bash
./scripts/quiesce.sh
cd pokertool-frontend
npm run build
cd ..
./scripts/resume.sh
```

### Scenario 3: Hot Reload (Development)

For development with auto-reload:

```bash
# Frontend (auto-reload built-in)
cd pokertool-frontend
npm start

# Backend (manual reload needed)
# Use full_update.sh when you make changes
```

### Scenario 4: Emergency Stop

If something goes wrong:

```bash
# Try graceful shutdown first
./scripts/quiesce.sh

# If that fails, find and kill process
ps aux | grep start.py
kill -9 <PID>

# Clean up PID file
rm -f .pokertool.pid
```

## State Preservation

### What Gets Saved

The update manager saves:
- Process PID
- Shutdown timestamp
- Shutdown reason
- Location: `.update_state.json`

### Future Enhancements

Planned state preservation:
- Active sessions
- WebSocket connections
- Cache data
- Current game state
- User preferences

## Logs

### Log Location

All update operations are logged to:
```
logs/update_manager.log
```

### Log Format

```
[TIMESTAMP] [LEVEL] MESSAGE
```

Example:
```
[2025-10-23 15:30:00] [INFO] ✓ Application stopped gracefully
[2025-10-23 15:30:10] [ERROR] Failed to pull changes: merge conflict
[2025-10-23 15:30:20] [WARN] Frontend build took longer than expected
```

## Troubleshooting

### Problem: Application Won't Stop

```bash
# Check if it's actually running
./scripts/status.sh

# Try quiesce again
./scripts/quiesce.sh

# Force kill if necessary
pkill -9 -f start.py
rm -f .pokertool.pid
```

### Problem: Update Fails

```bash
# Check git status
git status
git pull

# Check for conflicts
git diff

# Manual resolution
git merge --abort  # if in conflict
git pull --rebase
```

### Problem: Frontend Build Fails

```bash
cd pokertool-frontend

# Clean install
rm -rf node_modules package-lock.json
npm install

# Build with verbose output
npm run build -- --verbose
```

### Problem: Application Won't Start

```bash
# Check logs
tail -f logs/update_manager.log
tail -f logs/app.log

# Try starting manually
python3 start.py

# Check for port conflicts
lsof -i :5001
lsof -i :3000
```

## Best Practices

### Before Updating

1. **Check status**: Ensure app is running normally
   ```bash
   ./scripts/status.sh
   ```

2. **Backup critical data**: If you have important state
   ```bash
   cp .update_state.json .update_state.json.backup
   ```

3. **Check for uncommitted changes**:
   ```bash
   git status
   ```

### During Update

1. **Use full_update.sh**: It handles everything automatically
2. **Monitor logs**: Watch `logs/update_manager.log` for issues
3. **Wait for completion**: Don't interrupt the process

### After Update

1. **Verify status**:
   ```bash
   ./scripts/status.sh
   ```

2. **Check app health**:
   - Open browser to http://localhost:3000
   - Check backend API: http://localhost:5001/health

3. **Review logs**:
   ```bash
   tail -20 logs/update_manager.log
   ```

## Automation

### Cron Job (Scheduled Updates)

```bash
# Update every day at 3 AM
0 3 * * * cd /path/to/pokertool && ./scripts/full_update.sh >> logs/cron_update.log 2>&1
```

### Git Hook (Post-Merge)

Create `.git/hooks/post-merge`:

```bash
#!/bin/bash
echo "Code updated - consider running full_update.sh"
```

## Advanced Usage

### Custom Update Script

```python
from scripts.update_manager import UpdateManager

manager = UpdateManager()

# Custom workflow
if manager.quiesce():
    # Your custom update logic here
    run_database_migrations()
    clear_cache()

    # Standard update
    manager.update_code()

    # Your custom post-update logic
    warm_cache()

    # Restart
    manager.restart()
```

### Monitoring Integration

```bash
# Send notification on update
./scripts/full_update.sh && \
  curl -X POST https://your-monitoring-service/notify \
       -d "message=PokerTool updated successfully"
```

## Safety Features

1. **Graceful Shutdown**: 30-second timeout for clean exit
2. **State Preservation**: Saves state before shutdown
3. **Rollback Capability**: Can revert git changes
4. **Health Checks**: Verifies successful restart
5. **Comprehensive Logging**: All operations logged
6. **PID Tracking**: Prevents multiple instances

## Files Created

- `.update_state.json` - Saved application state
- `.pokertool.pid` - Process ID file
- `logs/update_manager.log` - Update operation logs

## Future Improvements

1. **Database Migration**: Automatic schema updates
2. **Rollback Mechanism**: Revert to previous version
3. **Blue-Green Deployment**: Zero-downtime updates
4. **Health Checks**: More comprehensive health verification
5. **Notification System**: Alert on update success/failure
6. **State Migration**: Preserve more application state
7. **Incremental Updates**: Only rebuild changed components

## Support

If you encounter issues:

1. Check `logs/update_manager.log`
2. Run `./scripts/status.sh`
3. Try manual steps instead of full_update
4. Check GitHub issues
5. Review this documentation

## Summary

The update manager provides a reliable, safe way to update PokerTool:

- ✅ Graceful shutdown preserves state
- ✅ Automatic code pull and rebuild
- ✅ Health checks ensure successful restart
- ✅ Comprehensive logging for troubleshooting
- ✅ Simple one-command operation

**Recommended usage**: `./scripts/full_update.sh`
