#!/usr/bin/env python3
# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: update_version_25.py
# version: v20.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
"""
Version Update Script - Update Pokertool to Version 25
Updates version strings across the entire codebase
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple

class VersionUpdater:
    def __init__(self, old_version = "25", new_version="25"):
        self.old_version = old_version
        self.new_version = new_version
        self.updated_files = []
        self.patterns = {
            'python': [
                (r'__version__\s*=\s*["\']24["\']', f'__version__ = "{new_version}"'),
                (r'VERSION\s*=\s*["\']24["\']', f'VERSION = "{new_version}"'),
                (r'version\s*=\s*["\']24["\']', f'version = "{new_version}"'),
                (r'Version 25', f'Version {new_version}'),
                (r'version 25', f'version {new_version}'),
                (r'v25', f'v{new_version}'),
                (r'pokertool-v25', f'pokertool-v{new_version}'),
                (r'return "25"', f'return "{new_version}"'),
            ],
            'json': [
                (r'"version":\s*"24"', f'"version": "{new_version}"'),
                (r'"version":\s*24', f'"version": "{new_version}"'),
            ],
            'markdown': [
                (r'# Pokertool v25', f'# Pokertool v{new_version}'),
                (r'## Version 25', f'## Version {new_version}'),
                (r'Version 25', f'Version {new_version}'),
                (r'v25', f'v{new_version}'),
                (r'pokertool-v25', f'pokertool-v{new_version}'),
            ],
            'yaml': [
                (r'version:\s*24', f'version: {new_version}'),
                (r'version:\s*"24"', f'version: "{new_version}"'),
                (r'tag:\s*v25', f'tag: v{new_version}'),
            ],
            'dockerfile': [
                (r'LABEL version = "25"', f'LABEL version="{new_version}"'),
                (r'ENV VERSION=24', f'ENV VERSION={new_version}'),
            ],
            'toml': [
                (r'version\s*=\s*"24"', f'version = "{new_version}"'),
            ]
        }
        
        self.file_extensions = {
            '.py': 'python',
            '.json': 'json',
            '.md': 'markdown',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.dockerfile': 'dockerfile',
            '.toml': 'toml'
        }

    def should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped"""
        skip_patterns = [
            '__pycache__',
            '.git',
            '.pytest_cache',
            'node_modules',
            '.DS_Store',
            'backups',
            '.egg-info',
            'build',
            'dist',
            '.venv',
            'venv'
        ]
        
        file_str = str(file_path)
        return any(pattern in file_str for pattern in skip_patterns)

    def update_file(self, file_path: Path) -> bool:
        """Update version strings in a single file"""
        if self.should_skip_file(file_path):
            return False
            
        file_ext = file_path.suffix.lower()
        if file_ext not in self.file_extensions:
            # Check if it's a Dockerfile without extension
            if file_path.name.lower() == 'dockerfile':
                file_type = 'dockerfile'
            else:
                return False
        else:
            file_type = self.file_extensions[file_ext]
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except (UnicodeDecodeError, PermissionError):
            print(f"⚠️  Skipping {file_path} - cannot read file")
            return False
        
        original_content = content
        patterns = self.patterns.get(file_type, [])
        
        # Apply patterns
        for old_pattern, new_string in patterns:
            content = re.sub(old_pattern, new_string, content)
        
        # Special handling for JSON files
        if file_type == 'json':
            try:
                data = json.loads(original_content)
                if self.update_json_data(data):
                    content = json.dumps(data, indent=2, ensure_ascii=False)
            except json.JSONDecodeError:
                pass  # Use regex patterns instead
        
        # Check if content changed
        if content != original_content:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.updated_files.append(str(file_path))
                print(f"✅ Updated: {file_path}")
                return True
            except PermissionError:
                print(f"⚠️  Permission denied: {file_path}")
                return False
        
        return False

    def update_json_data(self, data) -> bool:
        """Update version in JSON data structure"""
        updated = False
        
        if isinstance(data, dict):
            for key, value in data.items():
                if key == 'version' and str(value) == self.old_version:
                    data[key] = self.new_version
                    updated = True
                elif isinstance(value, (dict, list)):
                    if self.update_json_data(value):
                        updated = True
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    if self.update_json_data(item):
                        updated = True
        
        return updated

    def scan_and_update(self, root_dir: str = ".") -> Dict[str, int]:
        """Scan directory and update all applicable files"""
        root_path = Path(root_dir)
        stats = {
            'total_scanned': 0,
            'total_updated': 0,
            'by_extension': {}
        }
        
        print(f"🔍 Scanning {root_path.absolute()} for version updates...")
        
        for file_path in root_path.rglob('*'):
            if file_path.is_file():
                stats['total_scanned'] += 1
                
                if self.update_file(file_path):
                    stats['total_updated'] += 1
                    ext = file_path.suffix.lower() or 'no_extension'
                    stats['by_extension'][ext] = stats['by_extension'].get(ext, 0) + 1
        
        return stats

    def create_version_summary(self) -> None:
        """Create a summary of version update changes"""
        summary_file = Path("VERSION_UPDATE_SUMMARY.md")
        
        content = f"""# Version Update Summary - v{self.new_version}

## Update Details
- **Previous Version:** {self.old_version}
- **New Version:** {self.new_version}
- **Update Date:** {Path().absolute().name}
- **Total Files Updated:** {len(self.updated_files)}

## Updated Files
"""
        
        for file_path in sorted(self.updated_files):
            content += f"- `{file_path}`\n"
        
        content += f"""
## Key Changes
- Updated all version strings from {self.old_version} to {self.new_version}
- Updated package.json version
- Updated Python module versions
- Updated documentation references
- Updated Docker/YAML configurations

## Verification Commands
```bash
# Search for remaining old version references
grep -r "{self.old_version}" . --exclude-dir=.git --exclude-dir=__pycache__ --exclude-dir=backups

# Verify new version is set
grep -r "{self.new_version}" . --exclude-dir=.git --exclude-dir=__pycache__ --exclude-dir=backups | head -20
```

## Next Steps
1. Run comprehensive tests: `python -m pytest tests/ -v`
2. Commit changes: `python git_commit_develop.py`
3. Create release: `python git_commit_main.py`
"""
        
        with open(summary_file, 'w') as f:
            f.write(content)
        
        print(f"📄 Created version update summary: {summary_file}")

def main():
    print("🚀 Starting Pokertool Version 25 Update")
    print("=" * 50)
    
    updater = VersionUpdater(old_version = "25", new_version="25")
    
    # Update all files
    stats = updater.scan_and_update()
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 UPDATE SUMMARY")
    print("=" * 50)
    print(f"Total files scanned: {stats['total_scanned']}")
    print(f"Total files updated: {stats['total_updated']}")
    
    if stats['by_extension']:
        print("\nUpdates by file type:")
        for ext, count in sorted(stats['by_extension'].items()):
            print(f"  {ext}: {count} files")
    
    if updater.updated_files:
        print(f"\n✅ Successfully updated {len(updater.updated_files)} files to version 25")
        
        # Create summary document
        updater.create_version_summary()
        
        print("\n🎯 NEXT STEPS:")
        print("1. Review changes: git diff")
        print("2. Run tests: python -m pytest tests/ -v")
        print("3. Commit to develop: python git_commit_develop.py")
        print("4. Deploy to main: python git_commit_main.py")
    else:
        print("\n⚠️  No files were updated. Check if version 25 references exist.")
    
    print("\n🎉 Version update process complete!")

if __name__ == "__main__":
    main()
