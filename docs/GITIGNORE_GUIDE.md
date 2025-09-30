# .gitignore Configuration for PokerTool

**Last Updated:** September 29, 2025  
**Version:** v20.0.0

---

## Overview

The `.gitignore` file has been configured to exclude all state data, runtime files, and user-generated content while preserving the source code and documentation structure.

---

## What is Ignored

### 🗄️ Database Files
**Why:** Contains user data, session information, and application state that should not be in version control.

- `*.db`, `*.sqlite`, `*.sqlite3` - All SQLite database files
- `*.db-journal`, `*.db-shm`, `*.db-wal` - SQLite temporary files
- Database backups (`*.db.backup*`, `*.db.bak`)
- Specific databases:
  - `poker_decisions.db`
  - `opponent_profiles.db`
  - `poker_config.db`
  - `poker_analytics.db`
  - `poker_sessions.db`

### 📝 Log Files
**Why:** Logs contain runtime information and can grow large; each environment generates its own logs.

- `*.log`, `*.log.*` - All log files
- `logs/` - Log directory
- Specific logs:
  - `master_log.txt`
  - `poker_log.txt`
  - `scraper_log.txt`
  - `api_log.txt`
  - `error_log.txt`

### 🧠 Machine Learning Models
**Why:** Model files are large binary files that should be stored separately (model registry, S3, etc.).

- `*.pkl`, `*.pickle`, `*.joblib` - scikit-learn models
- `*.h5`, `*.hdf5` - Keras/TensorFlow models
- `*.pt`, `*.pth` - PyTorch models
- `*.onnx` - ONNX runtime models
- `*.pb` - TensorFlow protobuf
- `models/weights/`, `models/checkpoints/` - Model directories

### ♟️ GTO Solver Cache
**Why:** Cache files can be regenerated and are specific to each environment.

- `gto_cache/` - Cached GTO solutions
- `*.gto_cache` - GTO cache files
- `solver_cache/` - Solver computation cache

### 📸 Screen Scraper Data
**Why:** Contains screenshots and captured images that are user-specific and large.

- `screenshots/` - Captured screenshots
- `captures/` - Table captures
- `scraper_data/` - Scraped data
- `table_images/` - Table images
- `ocr_cache/` - OCR cache files

### 🔐 Secrets and API Keys
**Why:** Security - credentials should never be in version control.

- `.secrets` - Secrets file
- `*.key`, `*.pem` - Key files
- `.env.local`, `.env.*.local` - Local environment files
- `api_keys.json` - API credentials
- `secrets.json` - Application secrets

### 👤 User Data
**Why:** User-generated content is specific to each user/environment.

- `profiles/` - User profiles
- `user_data/` - User data directory
- `player_notes/` - Player notes
- `hand_histories/` - Hand history files
- `replays/` - Hand replays
- User configs:
  - `user_config.json`
  - `user_preferences.json`
  - `local_settings.json`

### 📊 Analytics and Reports
**Why:** Generated reports and exports are environment-specific.

- `analytics/`, `stats/`, `reports/` - Report directories
- `*.csv`, `*.xlsx`, `*.xls` - Export files
- `exports/` - Export directory

### 🔄 Cache and Temporary Files
**Why:** Temporary files are regenerated and not needed in version control.

- `cache/`, `.cache/`, `tmp/`, `temp/` - Cache directories
- `*.tmp`, `*.cache` - Temporary files
- `sessions/` - Session data
- `processing/`, `queue/`, `pending/` - Processing directories

### 🔧 Build and Development
**Why:** Build artifacts are generated and IDE configs are user-specific.

- `__pycache__/`, `*.pyc`, `*.pyo` - Python bytecode
- `build/`, `dist/` - Distribution files
- `.vscode/`, `.idea/` - IDE configurations
- `.pytest_cache/`, `.coverage` - Test artifacts
- `node_modules/` - Node dependencies (if applicable)

---

## What is NOT Ignored (Kept in Git)

### ✅ Source Code
- All `.py` files in `src/`
- All `.ts`, `.tsx`, `.js`, `.jsx` files for frontend
- All `.sh` bash scripts
- Configuration templates

### ✅ Documentation
- All `.md` markdown files
- Documentation in `docs/`
- README files
- API documentation

### ✅ Configuration Templates
- `pyproject.toml`
- `requirements.txt`
- `package.json`
- `tsconfig.json`
- Template/example config files

### ✅ Tests
- All test files (`test_*.py`)
- Test fixtures in `tests/fixtures/`
- Test configuration

### ✅ Assets
- Static images in `assets/`
- Icons and logos
- UI resources

---

## Special Cases

### Exception Rules

The `.gitignore` includes exceptions (using `!` prefix) to keep specific files:

```gitignore
# Keep example/template files
!example.db
!template.json
!sample_config.json

# Keep test fixtures
!tests/fixtures/*.db
!tests/fixtures/*.json
!tests/fixtures/*.csv

# Keep documentation
!docs/**/*.md
!docs/**/*.rst

# Keep static assets
!assets/**/*
```

### Why These Exceptions?

1. **Example files** - Provide templates for users
2. **Test fixtures** - Required for automated testing
3. **Documentation** - Even if in normally ignored directories
4. **Assets** - Static resources needed for the application

---

## Best Practices

### For Developers

1. **Never commit state data** - Always check before committing
2. **Use environment variables** - For secrets and API keys
3. **Document new patterns** - If adding new state file types
4. **Keep .gitignore updated** - As new features are added

### For Users

1. **Your data is safe** - Personal data won't accidentally be pushed
2. **Each environment is isolated** - Your local data stays local
3. **Clean clones** - New clones won't include old state data

---

## Verification

To verify what files are being tracked:

```bash
# See all tracked files
git ls-files

# See what would be committed
git status

# Check if a specific file is ignored
git check-ignore -v filename.db

# See all ignored files
git status --ignored
```

---

## Migration Guide

### If You Have Existing State Files in Git

If state files were previously committed, they need to be removed from history:

```bash
# Remove from tracking but keep local file
git rm --cached poker_decisions.db

# Remove from tracking (multiple files)
git rm --cached *.db

# Commit the removal
git commit -m "Remove state data from version control"

# For complete history cleanup (use with caution)
git filter-branch --tree-filter 'rm -f *.db' HEAD
```

### After Updating .gitignore

```bash
# Refresh git's file tracking
git rm -r --cached .
git add .
git commit -m "Update .gitignore and refresh tracking"
```

---

## Common Issues

### Issue: File Still Being Tracked

**Problem:** Updated .gitignore but file still shows in `git status`

**Solution:** File was previously tracked. Remove from tracking:
```bash
git rm --cached filename
```

### Issue: File Unexpectedly Ignored

**Problem:** File should be tracked but is ignored

**Solution:** Check ignore rules and add exception:
```bash
git check-ignore -v filename  # See which rule is matching
# Add exception in .gitignore if needed: !path/to/file
```

### Issue: Large Repo Size

**Problem:** Repository is large due to historical state files

**Solution:** Use git filter-branch or BFG Repo-Cleaner to remove from history

---

## Related Files

- `.gitattributes` - Git attributes configuration (if needed)
- `.dockerignore` - Similar ignore rules for Docker builds
- `.npmignore` - Ignore rules for npm packages (if applicable)

---

## Maintenance

This `.gitignore` should be reviewed and updated:

- When adding new features that generate state data
- When adding new file types (ML models, new databases, etc.)
- When security vulnerabilities are discovered in ignored patterns
- Quarterly as part of regular code review

**Next Review:** December 29, 2025

---

## Summary

The PokerTool `.gitignore` is configured to:

✅ **Protect user data** - No personal information in version control  
✅ **Reduce repo size** - No large binary files or generated content  
✅ **Enhance security** - No secrets or API keys tracked  
✅ **Improve performance** - No unnecessary files in diffs  
✅ **Maintain clarity** - Only source code and documentation tracked  

---

**Configuration Version:** v20.0.0  
**Last Updated:** September 29, 2025  
**Maintained By:** PokerTool Development Team
