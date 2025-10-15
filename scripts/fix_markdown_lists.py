#!/usr/bin/env python3
"""
Fix markdown list formatting issues.
Ensures all lists are surrounded by blank lines as per markdown best practices.
"""
import re
import sys
from pathlib import Path
from typing import List, Tuple


def fix_markdown_lists(content: str) -> Tuple[str, int]:
    """
    Fix markdown list formatting by ensuring lists are surrounded by blank lines.
    
    Args:
        content: The markdown content to fix
        
    Returns:
        Tuple of (fixed_content, number_of_fixes)
    """
    lines = content.split('\n')
    fixed_lines = []
    fixes = 0
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if current line is a list item
        is_list_item = bool(re.match(r'^(\s*)[-*+]\s+', line) or re.match(r'^(\s*)\d+\.\s+', line))
        
        # Check if previous line exists and is not blank
        prev_line_not_blank = (i > 0 and lines[i-1].strip() != '')
        
        # Check if previous line is not a list item
        prev_not_list = True
        if i > 0:
            prev_not_list = not bool(re.match(r'^(\s*)[-*+]\s+', lines[i-1]) or 
                                     re.match(r'^(\s*)\d+\.\s+', lines[i-1]))
        
        # If this is a list item and previous line is not blank and not a list item, add blank line
        if is_list_item and prev_line_not_blank and prev_not_list:
            fixed_lines.append('')
            fixes += 1
        
        fixed_lines.append(line)
        
        # Check if we need a blank line after the list
        if is_list_item and i < len(lines) - 1:
            next_line = lines[i + 1]
            next_is_list = bool(re.match(r'^(\s*)[-*+]\s+', next_line) or 
                               re.match(r'^(\s*)\d+\.\s+', next_line))
            next_is_blank = next_line.strip() == ''
            
            # If next line is not a list item and not blank, we need a blank line after
            if not next_is_list and not next_is_blank and next_line.strip() != '':
                i += 1
                fixed_lines.append('')
                fixed_lines.append(next_line)
                fixes += 1
                continue
        
        i += 1
    
    return '\n'.join(fixed_lines), fixes


def process_markdown_file(filepath: Path, dry_run: bool = False) -> Tuple[bool, int]:
    """
    Process a single markdown file.
    
    Args:
        filepath: Path to the markdown file
        dry_run: If True, don't write changes
        
    Returns:
        Tuple of (was_modified, number_of_fixes)
    """
    try:
        content = filepath.read_text(encoding='utf-8')
        fixed_content, fixes = fix_markdown_lists(content)
        
        if fixes > 0:
            if not dry_run:
                filepath.write_text(fixed_content, encoding='utf-8')
            return True, fixes
        return False, 0
    except Exception as e:
        print(f"Error processing {filepath}: {e}", file=sys.stderr)
        return False, 0


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix markdown list formatting')
    parser.add_argument('paths', nargs='*', default=['.'], help='Paths to check (default: current directory)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be fixed without making changes')
    parser.add_argument('--exclude', action='append', default=[], help='Directories to exclude')
    
    args = parser.parse_args()
    
    # Default exclusions
    exclude_dirs = {'node_modules', '.git', 'venv', '.venv', '__pycache__', 'dist', 'build'}
    exclude_dirs.update(args.exclude)
    
    total_files = 0
    total_fixes = 0
    modified_files = []
    
    for path_str in args.paths:
        path = Path(path_str)
        
        if path.is_file() and path.suffix == '.md':
            files = [path]
        elif path.is_dir():
            files = []
            for md_file in path.rglob('*.md'):
                # Check if file is in excluded directory
                if any(excluded in md_file.parts for excluded in exclude_dirs):
                    continue
                files.append(md_file)
        else:
            continue
        
        for filepath in files:
            total_files += 1
            was_modified, fixes = process_markdown_file(filepath, args.dry_run)
            
            if was_modified:
                modified_files.append((filepath, fixes))
                total_fixes += fixes
                if args.dry_run:
                    print(f"Would fix {fixes} issue(s) in {filepath}")
                else:
                    print(f"Fixed {fixes} issue(s) in {filepath}")
    
    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Processed {total_files} files")
    print(f"{'Would modify' if args.dry_run else 'Modified'} {len(modified_files)} files with {total_fixes} total fixes")
    
    return 0 if not args.dry_run or len(modified_files) == 0 else 1


if __name__ == '__main__':
    sys.exit(main())