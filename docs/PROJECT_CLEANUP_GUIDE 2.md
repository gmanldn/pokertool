# Project Cleanup & Structure Guide

This guide outlines state data management and recommended structural improvements for the PokerTool project.

## ✅ Recently Completed

### 1. Enhanced `.gitignore`

The following state data is now properly excluded from git:

- `video_frames/` - Temporary video processing files
- `debug_screenshots/` - Runtime debug images
- `structure_backup/` - Temporary backup directories
- `test_logs/` - Test execution logs
- `*.pokerheader.yml` - Metadata files
- `poker_config.json` - User-specific configuration

### 2. Configuration Template

Created [`poker_config.example.json`](../poker_config.example.json:1) as a template file that users should copy to `poker_config.json` and customize.

## 🎯 Recommended Actions

### Immediate Cleanup (Safe to Execute)

These directories contain state data and can be safely removed:

```bash
# Remove temporary video processing files
rm -rf video_frames/

# Remove debug artifacts
rm -rf debug_screenshots/

# Remove backup directories
rm -rf structure_backup/

# Remove test logs (regenerated on test runs)
rm -rf test_logs/

# Remove all .pokerheader.yml files
find . -name "*.pokerheader.yml" -type f -delete
```

### Database Files

Current database files in root (will be excluded from git):

- `poker.db`
- `pokertool.db`
- `poker_decisions.db`
- `opponent_profiles.db`
- `poker_config.db`

**Recommendation:** Move all database files to a dedicated `data/` directory:

```bash
# Create data directory
mkdir -p data

# Move database files
mv *.db data/ 2>/dev/null || true

# Update application to reference data/ directory
```

## 📁 Project Structure Analysis

The project currently mixes multiple distinct codebases:

### Current Root Structure

```
pokertool/
├── src/pokertool/          # Python poker analysis tool
├── src/                     # TypeScript VSCode extension (Cline)
├── pokertool-frontend/      # React frontend
├── webview-ui/              # VSCode webview UI
├── VectorCode/              # Neovim plugin
├── testing-platform/        # Testing infrastructure
├── k8s/                     # Kubernetes configs
└── [various config files]
```

### Issues

1. **Multiple package.json files** - Suggests monorepo but not structured as one
2. **Mixed languages** - Python, TypeScript, JavaScript in different subsystems
3. **Unclear ownership** - Root appears to be Cline/VSCode extension, not PokerTool
4. **Scattered documentation** - Multiple README files and doc directories

### Recommended Structure

#### Option A: Monorepo with Workspaces

```
pokertool-monorepo/
├── packages/
│   ├── pokertool-core/      # Python poker engine
│   ├── pokertool-frontend/  # React UI
│   ├── cline-extension/     # VSCode extension
│   ├── webview-ui/          # Extension webview
│   └── vectorcode/          # Neovim plugin
├── tools/                   # Shared tooling
├── docs/                    # Unified documentation
├── data/                    # Runtime data (gitignored)
├── .gitignore
├── package.json             # Root workspace config
└── README.md               # Main project overview
```

#### Option B: Separate Repositories

Split into distinct repositories:

- `pokertool` - Python poker analysis tool
- `pokertool-ui` - React frontend
- `cline` - VSCode extension
- `vectorcode` - Neovim plugin

## 🔧 Configuration Management

### Template Pattern

All user-specific configuration should use the template pattern:

1. **Check-in:** `config.example.json` (template with defaults)
2. **Gitignore:** `config.json` (user-specific settings)
3. **First run:** Copy template to actual config

Example files to convert:

- `poker_config.json` → Already done ✅
- Any other `.json` files containing user settings

### Environment Variables

Consider using environment variables for deployment-specific settings:

```bash
# .env.example (checked in)
DATABASE_PATH=./data/poker_decisions.db
GUI_THEME=dark
MAX_TABLES=12

# .env (gitignored)
DATABASE_PATH=/custom/path/poker.db
GUI_THEME=light
```

## 📊 State Data Categories

### 1. User Configuration (Gitignore)

- `poker_config.json` - GUI and feature settings
- `user_preferences.json` - User-specific preferences
- `.env` - Environment variables

### 2. Runtime Data (Gitignore)

- `*.db` - Database files
- `*.log` - Log files
- `sessions/` - Session data
- `cache/` - Cache directories
- `screenshots/` - Screen captures

### 3. Generated Artifacts (Gitignore)

- `test_logs/` - Test results
- `debug_screenshots/` - Debug images
- `video_frames/` - Processed video frames
- `build/`, `dist/` - Build outputs

### 4. Source Code (Track in Git)

- `src/` - Application source
- `tests/` - Test code
- `docs/` - Documentation
- `*.example.json` - Configuration templates
- `assets/` - Static assets

## 🚀 Migration Steps

If you decide to restructure:

### 1. Backup Current State

```bash
# Create backup
tar -czf pokertool-backup-$(date +%Y%m%d).tar.gz .
```

### 2. Clean State Data

```bash
# Remove all gitignored state data
git clean -fdX

# This removes:
# - Database files
# - Log files
# - Cache directories
# - Build artifacts
# - Other gitignored files
```

### 3. Verify Clean State

```bash
# Check for untracked files
git status

# Should only show intentional untracked files
```

### 4. Update Documentation

```bash
# Update README with new structure
# Update CONTRIBUTING.md with setup instructions
# Update deployment docs
```

## 📝 Best Practices

### 1. Separation of Concerns

- **Code:** Version controlled
- **Configuration:** Templates in git, actuals gitignored
- **Data:** Always gitignored
- **Secrets:** Never committed (use env vars or secret managers)

### 2. Clear Documentation

- README at each level explaining that directory's purpose
- Configuration examples with comments
- Setup instructions for new developers

### 3. Consistent Naming

- `*.example.*` for templates
- `data/` for all runtime data
- `logs/` for all log files
- `.local.*` for local overrides

## 🔍 Files Requiring Attention

### Metadata Files (Can Remove)

- `*.pokerheader.yml` - Appears to be custom metadata system
- Consider if this metadata should be in git or generated at build time

### Lock Files

- Multiple `package-lock.json.pokerheader.yml` files
- These seem redundant if using standard npm

### Archive Directories

- `archive/` - Review contents, consider if still needed
- `structure_backup/` - Can be removed if no longer needed

## 📚 Related Documentation

- [`GITIGNORE_GUIDE.md`](GITIGNORE_GUIDE.md:1) - Detailed gitignore documentation
- [`README.md`](../README.md:1) - Main project documentation
- [`FEATURES.md`](FEATURES.md:1) - Feature documentation

## 🤝 Contributing

When adding new features:

1. Identify if your feature generates state data
2. Add appropriate gitignore entries
3. Create configuration templates (`.example` files)
4. Document in setup instructions
5. Consider data directory organization

## ✨ Summary

The project now has improved state data management with:

- ✅ Enhanced `.gitignore` excluding state data
- ✅ Configuration template pattern (`poker_config.example.json`)
- ✅ Clear documentation of structure issues
- ✅ Actionable recommendations for improvement

Next steps depend on project goals:

- **Quick Win:** Execute immediate cleanup commands
- **Medium Term:** Move databases to `data/` directory
- **Long Term:** Consider monorepo restructuring or repository split