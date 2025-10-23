# PokerTool Feature Management Script

## Overview

The `add_feature.py` script automates Git operations for the PokerTool project, including:
- Committing features to the develop branch
- Creating versioned releases with automatic version bumping
- Managing release branches
- Pushing changes to remote repository

## Prerequisites

1. **Git installed**: Ensure Git is installed and accessible from command line
2. **GITREPO_LOCATION.md**: Must exist in project root with repository URL
3. **Git configuration**: Your Git user.name and user.email must be configured

## Installation

The script is ready to use. Make it executable (Unix/Mac):

```bash
chmod +x add_feature.py
```

## Usage

### Adding a Feature to Develop Branch

Add all changes:
```bash
python add_feature.py --message "Add new poker hand analyzer"
```

Add specific files:
```bash
python add_feature.py --message "Fix API bug" --files src/pokertool/api.py tests/test_api.py
```

Short form:
```bash
python add_feature.py -m "Your commit message"
```

### Creating a Release

**Minor Release** (1.2.3 → 1.3.0):
```bash
python add_feature.py --release --message "Release with new features"
```

**Major Release** (1.2.3 → 2.0.0):
```bash
python add_feature.py --release --bump major --message "Major version update"
```

**Patch Release** (1.2.3 → 1.2.4):
```bash
python add_feature.py --release --bump patch --message "Bug fix release"
```

### Dry Run (Preview Mode)

Preview operations without executing:
```bash
python add_feature.py --message "Test commit" --dry-run
```

For releases:
```bash
python add_feature.py --release --message "Test release" --dry-run
```

## Command-Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--message` | `-m` | Commit or release message (required) |
| `--release` | `-r` | Create a release instead of feature commit |
| `--bump` | `-b` | Version bump type: major, minor, patch (default: minor) |
| `--files` | `-f` | Specific files to commit (default: all changes) |
| `--dry-run` | `-d` | Preview operations without executing |

## How It Works

### Feature Addition Workflow

1. Checks current Git branch
2. Switches to `develop` branch if needed
3. Stages specified files (or all changes)
4. Commits changes with your message
5. Pushes to remote `develop` branch

### Release Creation Workflow

1. Reads current version from Git tags
2. Increments version based on bump type
3. Creates release branch: `release/v{version}`
4. Creates annotated Git tag: `v{version}`
5. Pushes release branch with upstream tracking
6. Pushes all tags to remote
7. Switches back to `develop` branch

## Version Numbering

The script uses semantic versioning (MAJOR.MINOR.PATCH):

- **Major**: Incompatible API changes (1.2.3 → 2.0.0)
- **Minor**: New features, backwards compatible (1.2.3 → 1.3.0)
- **Patch**: Bug fixes, backwards compatible (1.2.3 → 1.2.4)

## Examples

### Example 1: Quick Feature Commit
```bash
# Fix a bug and commit to develop
python add_feature.py -m "Fix memory leak in scraper"
```

### Example 2: Targeted File Commit
```bash
# Only commit specific files
python add_feature.py -m "Update API documentation" -f docs/API.md src/pokertool/api.py
```

### Example 3: Create Minor Release
```bash
# Current version: v1.4.2
python add_feature.py --release -m "Add new GTO solver features"
# Creates: release/v1.5.0 and tag v1.5.0
```

### Example 4: Create Major Release
```bash
# Current version: v1.4.2
python add_feature.py --release --bump major -m "Breaking changes: New API structure"
# Creates: release/v2.0.0 and tag v2.0.0
```

### Example 5: Test Before Executing
```bash
# Preview what would happen
python add_feature.py --release -m "Test release" --dry-run
```

## Configuration

### GITREPO_LOCATION.md Format

The file can contain the URL in several formats:

Plain URL:
```
https://github.com/gmanldn/pokertool.git
```

Markdown code block:
```markdown
Repository URL:
```
https://github.com/gmanldn/pokertool.git
```
```

SSH format:
```
git@github.com:gmanldn/pokertool.git
```

## Troubleshooting

### "Git is not installed or not in PATH"
- Install Git: https://git-scm.com/downloads
- Ensure Git is in your system PATH

### "GITREPO_LOCATION.md not found"
- Create the file in project root
- Add your repository URL to the file

### "Error pushing branch"
- Check your Git credentials
- Ensure you have push access to the repository
- Verify remote repository is accessible

### "No changes to commit"
- Make sure you have modified files
- Check `git status` to see pending changes
- Use `--files` to specify files to commit

### Permission Issues
- Make script executable: `chmod +x add_feature.py`
- Ensure you have write access to the repository

## Best Practices

1. **Always use descriptive commit messages**
   ```bash
   # Good
   python add_feature.py -m "Add opponent modeling with temporal fusion"
   
   # Bad
   python add_feature.py -m "update"
   ```

2. **Test releases with dry-run first**
   ```bash
   python add_feature.py --release -m "v2.0 release" --dry-run
   ```

3. **Use appropriate version bumps**
   - Patch: Small bug fixes
   - Minor: New features, no breaking changes
   - Major: Breaking changes, major updates

4. **Commit related changes together**
   ```bash
   python add_feature.py -m "Add feature X" -f src/feature.py tests/test_feature.py
   ```

## Script Features

- ✅ Colored terminal output for better readability
- ✅ Comprehensive error handling and validation
- ✅ Dry-run mode for safe testing
- ✅ Automatic version increment
- ✅ Git tag management
- ✅ Branch switching and creation
- ✅ Flexible file staging
- ✅ Detailed operation feedback

## Exit Codes

- `0`: Success
- `1`: Error occurred or user cancelled

## Support

For issues or questions:
1. Check this README
2. Run with `--dry-run` to preview operations
3. Check Git status: `git status`
4. Review recent commits: `git log --oneline -5`

## License

Part of the PokerTool project - see main project LICENSE file.
