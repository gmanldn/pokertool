# Update Manager Scripts

Quick reference for updating PokerTool safely while running.

## One-Command Update (Recommended)

```bash
./scripts/full_update.sh
```

This will:
1. Gracefully stop the app
2. Pull latest code
3. Rebuild frontend
4. Restart the app

## Individual Commands

```bash
./scripts/status.sh      # Check if app is running
./scripts/quiesce.sh     # Gracefully stop app
./scripts/update.sh      # Pull code & rebuild
./scripts/resume.sh      # Restart app
```

## Usage Examples

### Check Status
```bash
./scripts/status.sh
```

### Apply Updates
```bash
./scripts/full_update.sh
```

### Manual Update Process
```bash
./scripts/quiesce.sh  # Stop
git pull              # Update (alternative to update.sh)
./scripts/update.sh   # Or use this to pull + rebuild
./scripts/resume.sh   # Start
```

## Documentation

See [docs/UPDATE_PROCEDURES.md](../docs/UPDATE_PROCEDURES.md) for complete documentation.

## Logs

All operations logged to: `logs/update_manager.log`

## State Files

- `.pokertool.pid` - Process ID
- `.update_state.json` - Saved state during updates
