# Version & Documentation Status

This file tracks the documentation status for each version of PokerTool, making it easy to identify what needs updating when new features are added.

**Current Version:** 101.0.0

---

## Documentation Status Legend

- ✅ **Complete** - Fully documented
- ⚠️ **Partial** - Partially documented, needs updates
- ❌ **Missing** - Not documented
- 🔄 **In Progress** - Currently being documented

---

## Version History & Documentation Status

### [101.0.0] - Current (2025-10-23)

**Documentation Status: ✅ Complete**

#### Features Added:
- Update Manager system for live code updates
- Graceful shutdown (quiesce) functionality
- State preservation during updates
- Health monitoring and process tracking
- Convenience scripts (full_update.sh, quiesce.sh, update.sh, resume.sh, status.sh)

#### Documentation Status:

| Document | Status | Last Updated | Notes |
|----------|--------|--------------|-------|
| README.md | ✅ Complete | 2025-10-23 | Update Manager section added |
| DEVELOPMENT_WORKFLOW.md | ✅ Complete | 2025-10-23 | Update Manager in Tools & Commands |
| MANUAL.md | ✅ Complete | 2025-10-23 | Complete Update Manager section |
| UPDATE_PROCEDURES.md | ✅ Complete | 2025-10-23 | Comprehensive update guide |
| scripts/README.md | ✅ Complete | 2025-10-23 | Quick reference for scripts |

#### What to Update for Next Version:
- When adding new features, check if they affect update procedures
- Update troubleshooting sections if new issues are discovered
- Add automation examples if CI/CD is implemented

---

### [98.0.0] - 2025-10-21

**Documentation Status: ⚠️ Partial**

#### Features Added:
- PokerDatabase backward compatibility wrapper
- pokertool.system package for ML modules
- pokertool.modules package for nash_solver
- cleanup_old_processes() in start.py
- Fixed ML API endpoint signatures
- Enhanced smoke test coverage

#### Documentation Status:

| Document | Status | Last Updated | Notes |
|----------|--------|--------------|-------|
| README.md | ⚠️ Partial | Prior to 98.0.0 | Database wrapper not documented |
| DEVELOPMENT_WORKFLOW.md | ⚠️ Partial | Prior to 98.0.0 | New package structure not documented |
| MANUAL.md | ❌ Missing | N/A | ML modules import paths not documented |
| API.md | ⚠️ Partial | Unknown | Fixed endpoints not explicitly noted |

#### What Needs Documentation:
- PokerDatabase backward compatibility wrapper usage
- Import path changes for ML modules (pokertool.system.*)
- Nash solver import from pokertool.modules
- cleanup_old_processes() function behavior
- Fixed API endpoint signatures

---

### [88.6.0] - 2025-10-19

**Documentation Status: ⚠️ Partial**

#### Features Added:
- Sentry error tracking on frontend
- WebSocket end-to-end tests
- Documented developer onboarding
- Reordered backend WebSocket routes
- System-health checker improvements

#### Documentation Status:

| Document | Status | Last Updated | Notes |
|----------|--------|--------------|-------|
| README.md | ⚠️ Partial | 88.6.0 | Sentry setup not in main README |
| DEVELOPMENT_WORKFLOW.md | ✅ Complete | 88.6.0 | Updated with onboarding |
| ENVIRONMENT_VARIABLES.md | ✅ Complete | 88.6.0 | Simplified and refreshed |
| TESTING.md | ⚠️ Partial | Unknown | WebSocket tests not fully documented |

#### What Needs Documentation:
- Sentry error tracking setup and configuration
- WebSocket route ordering and why it matters
- System-health broadcast pipeline details

---

### [88.4.0] - 2025-10-19

**Documentation Status: ✅ Complete**

#### Features Added:
- Expanded README introduction
- Updated architecture knowledge base
- Refreshed sample range presets

#### Documentation Status:

| Document | Status | Last Updated | Notes |
|----------|--------|--------------|-------|
| README.md | ✅ Complete | 88.4.0 | Full decision stack documented |
| tests/architecture/data/architecture.json | ✅ Complete | 88.4.0 | Latest module metadata |

---

## Documentation Checklist for New Versions

When adding a new version, use this checklist to ensure complete documentation:

### Core Documentation Files

- [ ] **README.md** - Update main features section
  - [ ] Add new features to Quick Start
  - [ ] Update architecture diagram if needed
  - [ ] Add new dependencies or requirements
  - [ ] Update installation instructions if changed

- [ ] **CHANGELOG.md** - Add version entry
  - [ ] List all features added
  - [ ] List all bugs fixed
  - [ ] List all breaking changes
  - [ ] Note deprecated features

- [ ] **DEVELOPMENT_WORKFLOW.md** - Update developer docs
  - [ ] Add new commands to daily workflow
  - [ ] Document new tools or scripts
  - [ ] Update testing procedures
  - [ ] Add troubleshooting for new issues

- [ ] **MANUAL.md** - Update user manual
  - [ ] Add user-facing feature documentation
  - [ ] Update screenshots/examples if applicable
  - [ ] Add troubleshooting for new features
  - [ ] Update configuration options

### Specialized Documentation (if applicable)

- [ ] **API.md** - If API endpoints changed
  - [ ] Document new endpoints
  - [ ] Update endpoint signatures
  - [ ] Add request/response examples
  - [ ] Note deprecated endpoints

- [ ] **TESTING.md** - If testing changed
  - [ ] Document new test types
  - [ ] Update test commands
  - [ ] Add test writing guidelines
  - [ ] Update coverage requirements

- [ ] **ENVIRONMENT_VARIABLES.md** - If env vars changed
  - [ ] Add new environment variables
  - [ ] Update default values
  - [ ] Document variable purposes
  - [ ] Add examples

- [ ] **ARCHITECTURE.md** - If architecture changed
  - [ ] Update component diagrams
  - [ ] Document new modules
  - [ ] Update data flow diagrams
  - [ ] Note architectural decisions

### Code Documentation

- [ ] **Docstrings** - In code files
  - [ ] Add docstrings to all new functions
  - [ ] Add docstrings to all new classes
  - [ ] Update existing docstrings if changed
  - [ ] Add examples in docstrings

- [ ] **Type Hints** - In Python files
  - [ ] Add type hints to all new functions
  - [ ] Add type hints to all new classes
  - [ ] Update existing type hints if changed

- [ ] **Comments** - In code files
  - [ ] Add comments for complex logic
  - [ ] Add TODOs for future improvements
  - [ ] Remove outdated comments

---

## How to Use This File

### For AI Assistants:

1. **Check current version** in VERSION file
2. **Look up version** in this file to see documentation status
3. **Identify gaps** - Look for ⚠️ or ❌ markers
4. **Update documentation** as needed
5. **Update this file** when documentation is completed
6. **Mark as ✅** when fully documented

### For Developers:

1. **Before releasing** a new version, create entry here
2. **Mark documentation status** for all relevant files
3. **Use checklist** to ensure nothing is missed
4. **Update markers** as documentation progresses
5. **Mark version as ✅ Complete** when all docs are done

### Example Workflow:

```bash
# 1. Check current version
cat VERSION
# Output: 101.0.0

# 2. Read documentation status
cat VERSION.md
# Look for [101.0.0] section

# 3. Update documentation as needed
# ... edit files ...

# 4. Update VERSION.md status markers
# Change ⚠️ to ✅ as you complete each document

# 5. Commit with version tag
git add docs/
git commit -m "docs: complete documentation for v101.0.0"
```

---

## Version Numbering

PokerTool follows **Semantic Versioning** (MAJOR.MINOR.PATCH):

- **MAJOR** (101.x.x) - Breaking changes, major rewrites
- **MINOR** (x.0.x) - New features, backward compatible
- **PATCH** (x.x.0) - Bug fixes, backward compatible

When incrementing version:
1. Update VERSION file
2. Add entry to CHANGELOG.md
3. Add entry to this VERSION.md with documentation status
4. Tag release in git: `git tag -a v101.0.0 -m "Release v101.0.0"`

---

## Documentation Maintenance Schedule

- **Every Release**: Update VERSION.md with new version entry
- **Every Feature**: Mark documentation status for that feature
- **Monthly Review**: Check for ⚠️ markers and complete partial docs
- **Quarterly Audit**: Review all documentation for accuracy
- **Before Major Release**: Ensure all docs marked ✅

---

## Notes for Future Documentation

### Known Documentation Gaps:

1. **ML Modules** (v98.0.0):
   - Import path changes not fully documented
   - Backward compatibility wrapper usage unclear
   - Migration guide needed for old code

2. **Sentry Integration** (v88.6.0):
   - Frontend setup not in main docs
   - Configuration options not documented
   - Troubleshooting guide missing

3. **WebSocket Architecture** (v88.6.0):
   - Route ordering rationale not documented
   - System-health broadcast pipeline unclear

### Upcoming Documentation Needs:

- Migration guide from old to new import paths
- Complete API reference documentation
- Video tutorials for update manager
- Troubleshooting decision tree
- Performance tuning guide

---

**Last Updated:** 2025-10-23 by Claude Code
**Next Review:** When version 102.0.0 is released
