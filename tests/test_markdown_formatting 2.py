#!/usr/bin/env python3
"""
Unit tests for markdown formatting validation.
Ensures markdown files follow best practices for list formatting.
"""
import pytest
from pathlib import Path
import re


def find_markdown_files(root_path: Path, exclude_dirs=None):
    """Find all markdown files excluding certain directories."""
    if exclude_dirs is None:
        exclude_dirs = {'node_modules', '.git', 'venv', '.venv', '__pycache__', 'dist', 'build', 
                       '.venv.backup-homebrew', 'VectorCode', 'locales'}
    
    markdown_files = []
    for md_file in root_path.rglob('*.md'):
        if any(excluded in md_file.parts for excluded in exclude_dirs):
            continue
        markdown_files.append(md_file)
    return markdown_files


def check_list_formatting(content: str):
    """
    Check if lists in markdown content are properly formatted with blank lines.
    
    Returns a list of line numbers where formatting issues are found.
    """
    lines = content.split('\n')
    issues = []
    
    for i, line in enumerate(lines):
        # Check if current line is a list item
        is_list_item = bool(re.match(r'^(\s*)[-*+]\s+', line) or re.match(r'^(\s*)\d+\.\s+', line))
        
        if not is_list_item:
            continue
        
        # Check if previous line exists and is not blank
        if i > 0:
            prev_line = lines[i-1]
            prev_is_blank = prev_line.strip() == ''
            prev_is_list = bool(re.match(r'^(\s*)[-*+]\s+', prev_line) or 
                               re.match(r'^(\s*)\d+\.\s+', prev_line))
            prev_is_heading = prev_line.strip().startswith('#')
            prev_is_code_fence = prev_line.strip().startswith('```')
            
            # If previous line is not blank and not a list item and not special, flag it
            if not prev_is_blank and not prev_is_list and not prev_is_heading and not prev_is_code_fence:
                if prev_line.strip() != '':  # Only flag if prev line has content
                    issues.append((i + 1, f"List should have blank line before it (previous line: '{prev_line[:50]}...')"))
        
        # Check if next line needs a blank line after the list
        if i < len(lines) - 1:
            next_line = lines[i + 1]
            next_is_list = bool(re.match(r'^(\s*)[-*+]\s+', next_line) or 
                               re.match(r'^(\s*)\d+\.\s+', next_line))
            next_is_blank = next_line.strip() == ''
            next_is_heading = next_line.strip().startswith('#')
            next_is_code_fence = next_line.strip().startswith('```')
            
            # If next line is not a list item, not blank, and not special, flag it
            if not next_is_list and not next_is_blank and not next_is_heading and not next_is_code_fence:
                if next_line.strip() != '':  # Only flag if next line has content
                    issues.append((i + 1, f"List should have blank line after it (next line: '{next_line[:50]}...')"))
    
    return issues


def test_markdown_list_formatting():
    """Test that all markdown files have properly formatted lists."""
    repo_root = Path(__file__).parent.parent
    markdown_files = find_markdown_files(repo_root)
    
    failed_files = {}
    
    for md_file in markdown_files:
        try:
            content = md_file.read_text(encoding='utf-8')
            issues = check_list_formatting(content)
            
            if issues:
                failed_files[str(md_file.relative_to(repo_root))] = issues
        except Exception as e:
            pytest.fail(f"Error reading {md_file}: {e}")
    
    if failed_files:
        error_msg = "\n\n❌ Markdown list formatting issues found:\n\n"
        for file_path, issues in failed_files.items():
            error_msg += f"📄 {file_path}:\n"
            for line_num, issue in issues[:5]:  # Show first 5 issues per file
                error_msg += f"  Line {line_num}: {issue}\n"
            if len(issues) > 5:
                error_msg += f"  ... and {len(issues) - 5} more issues\n"
            error_msg += "\n"
        
        error_msg += "💡 Fix with: python scripts/fix_markdown_lists.py --exclude locales --exclude node_modules --exclude .venv --exclude VectorCode\n"
        pytest.fail(error_msg)


def test_fix_markdown_script_exists():
    """Test that the markdown fixing script exists."""
    script_path = Path(__file__).parent.parent / 'scripts' / 'fix_markdown_lists.py'
    assert script_path.exists(), f"Markdown fix script not found at {script_path}"


def test_markdown_list_formatting_examples():
    """Test the list formatting checker with examples."""
    
    # Good example - list with blank lines
    good_content = """
Some text here.

- Item 1
- Item 2
- Item 3

More text here.
"""
    issues = check_list_formatting(good_content)
    assert len(issues) == 0, "Good example should have no issues"
    
    # Bad example - list without blank lines
    bad_content = """
Some text here.
- Item 1
- Item 2
More text here.
"""
    issues = check_list_formatting(bad_content)
    assert len(issues) > 0, "Bad example should have issues"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])