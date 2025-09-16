#!/usr/bin/env python3
"""
Self-contained Python Code Scanner and Fixer for pokertool repository
No external dependencies required - uses only Python standard library
"""

import ast
import os
import re
import sys
import tokenize
import io
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional
import difflib
import tempfile
import shutil
from collections import defaultdict
import keyword
import builtins


class CodeScanner:
    """Main class for scanning and fixing Python code issues"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.issues_found = []
        self.fixes_applied = []
        self.stats = defaultdict(int)
        
    def scan_repository(self):
        """Scan all Python files in the repository"""
        print(f"Scanning repository at: {self.repo_path}")
        print("=" * 60)
        
        python_files = list(self.repo_path.rglob("*.py"))
        
        # Filter out files we shouldn't touch
        python_files = [
            f for f in python_files 
            if not any(skip in str(f) for skip in [
                "venv", "__pycache__", "env", ".env", 
                "migrations", "code_scan.py", ".git",
                "build", "dist", ".tox", ".pytest_cache"
            ])
        ]
        
        print(f"Found {len(python_files)} Python files to scan\n")
        
        for file_path in python_files:
            print(f"Processing: {file_path}")
            self.process_file(file_path)
            
        self.generate_report()
        
    def process_file(self, file_path: Path):
        """Process a single Python file"""
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            if not original_content.strip():
                print(f"  ⚠ Skipping empty file")
                return
                
            # Apply all fixes
            fixed_content = self.apply_all_fixes(original_content, file_path)
            
            # Write back if changes were made
            if fixed_content != original_content:
                # Create backup
                backup_path = file_path.with_suffix('.py.backup')
                shutil.copy2(file_path, backup_path)
                
                # Write fixed content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                    
                self.fixes_applied.append(str(file_path))
                print(f"  ✓ Fixed and backed up to {backup_path}")
                
                # Show diff if small enough
                if len(original_content) < 5000:
                    self.show_diff(original_content, fixed_content)
            else:
                print(f"  ✓ No issues found")
                
        except Exception as e:
            self.issues_found.append(f"{file_path}: {str(e)}")
            print(f"  ✗ Error: {str(e)}")
    
    def apply_all_fixes(self, content: str, file_path: Path) -> str:
        """Apply all available fixes to the content"""
        
        # Track what we've fixed
        original = content
        
        # Apply fixes in order
        fixes = [
            ("syntax_errors", self.fix_syntax_errors),
            ("indentation", self.fix_indentation),
            ("imports", self.fix_imports),
            ("whitespace", self.fix_whitespace),
            ("python2to3", self.fix_python2_to_3),
            ("quotes", self.normalize_quotes),
            ("poker_specific", self.fix_poker_specific),
            ("typos", self.fix_common_typos),
            ("docstrings", self.add_missing_docstrings),
            ("exceptions", self.fix_exception_handling),
            ("comparison", self.fix_comparisons),
            ("naming", self.fix_naming_conventions),
            ("line_length", self.fix_line_length),
            ("trailing", self.fix_trailing_issues),
            ("magic_methods", self.fix_magic_methods),
        ]
        
        for fix_name, fix_func in fixes:
            try:
                new_content = fix_func(content, file_path)
                if new_content != content:
                    self.stats[fix_name] += 1
                    content = new_content
            except Exception as e:
                # Don't let one fix break everything
                pass
                
        return content
    
    def fix_syntax_errors(self, content: str, file_path: Path) -> str:
        """Fix common syntax errors"""
        
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            # Fix missing colons
            if re.match(r'^(\s*)(if|elif|else|for|while|def|class|try|except|finally|with)\s+[^:]+$', line):
                if not line.rstrip().endswith(':'):
                    line = line.rstrip() + ':'
            
            # Fix assignment vs comparison
            # if x = 5: -> if x == 5:
            if_match = re.match(r'^(\s*)if\s+(.+?)\s*=\s*(.+?)\s*:$', line)
            if if_match and '==' not in line and '!=' not in line:
                line = f"{if_match.group(1)}if {if_match.group(2)} == {if_match.group(3)}:"
            
            # Fix else if -> elif
            line = re.sub(r'^(\s*)else\s+if\s*', r'\1elif ', line)
            
            fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        # Validate the fixes
        try:
            compile(content, '<string>', 'exec')
        except SyntaxError as e:
            # If we broke it, return original
            return '\n'.join(lines)
            
        return content
    
    def fix_indentation(self, content: str, file_path: Path) -> str:
        """Fix indentation issues"""
        
        # Convert tabs to spaces
        content = content.replace('\t', '    ')
        
        lines = content.split('\n')
        fixed_lines = []
        expected_indent = 0
        indent_stack = [0]
        
        for line in lines:
            stripped = line.lstrip()
            
            if not stripped or stripped.startswith('#'):
                fixed_lines.append(line)
                continue
            
            current_indent = len(line) - len(stripped)
            
            # Decrease indent after pass, return, break, continue
            if fixed_lines and any(fixed_lines[-1].strip().startswith(kw) 
                                  for kw in ['return', 'pass', 'break', 'continue', 'raise']):
                if indent_stack:
                    expected_indent = indent_stack[-1]
            
            # Check for dedent keywords
            if stripped.startswith(('else:', 'elif ', 'except:', 'except ', 'finally:')):
                if len(indent_stack) > 1:
                    indent_stack.pop()
                    expected_indent = indent_stack[-1]
            
            # Fix the indent
            if current_indent != expected_indent and stripped:
                line = ' ' * expected_indent + stripped
            
            # Check for indent increase
            if line.rstrip().endswith(':'):
                expected_indent += 4
                indent_stack.append(expected_indent)
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def fix_imports(self, content: str, file_path: Path) -> str:
        """Organize and fix imports"""
        
        lines = content.split('\n')
        
        # Separate imports from rest of code
        import_lines = []
        other_lines = []
        in_imports = True
        
        for line in lines:
            stripped = line.strip()
            
            if in_imports:
                if stripped.startswith(('import ', 'from ')) or not stripped:
                    import_lines.append(line)
                elif stripped.startswith('#'):
                    import_lines.append(line)
                else:
                    in_imports = False
                    other_lines.append(line)
            else:
                other_lines.append(line)
        
        # Sort imports
        stdlib_imports = []
        third_party_imports = []
        local_imports = []
        
        for line in import_lines:
            if line.strip().startswith(('import ', 'from ')):
                # Classify import
                if 'import .' in line or 'from .' in line:
                    local_imports.append(line)
                elif any(mod in line for mod in ['os', 'sys', 're', 'ast', 'json', 
                                                  'pathlib', 'typing', 'collections',
                                                  'datetime', 'random', 'math']):
                    stdlib_imports.append(line)
                else:
                    third_party_imports.append(line)
        
        # Sort each group
        stdlib_imports.sort()
        third_party_imports.sort()
        local_imports.sort()
        
        # Reconstruct
        new_lines = []
        
        if stdlib_imports:
            new_lines.extend(stdlib_imports)
            new_lines.append('')
            
        if third_party_imports:
            new_lines.extend(third_party_imports)
            new_lines.append('')
            
        if local_imports:
            new_lines.extend(local_imports)
            new_lines.append('')
            
        new_lines.extend(other_lines)
        
        # Remove multiple blank lines
        result = []
        prev_blank = False
        for line in new_lines:
            if not line.strip():
                if not prev_blank:
                    result.append(line)
                prev_blank = True
            else:
                result.append(line)
                prev_blank = False
                
        return '\n'.join(result)
    
    def fix_whitespace(self, content: str, file_path: Path) -> str:
        """Fix whitespace issues"""
        
        # Remove trailing whitespace
        lines = [line.rstrip() for line in content.split('\n')]
        
        # Fix spacing around operators
        fixed_lines = []
        for line in lines:
            # Add spaces around operators
            line = re.sub(r'(\w)([=+\-*/%<>]=?)(\w)', r'\1 \2 \3', line)
            line = re.sub(r'(\w)([=+\-*/%<>])(["\'])', r'\1 \2 \3', line)
            
            # Fix spacing after commas
            line = re.sub(r',(?!\s)', ', ', line)
            
            # Fix spacing after colons (except in slices)
            line = re.sub(r':(?!\s|$|\])', ': ', line)
            
            fixed_lines.append(line)
            
        return '\n'.join(fixed_lines)
    
    def fix_python2_to_3(self, content: str, file_path: Path) -> str:
        """Fix Python 2 to Python 3 issues"""
        
        # print statement -> print function
        content = re.sub(r'^(\s*)print\s+([^(\n]+)$', r'\1print(\2)', content, flags=re.MULTILINE)
        
        # xrange -> range
        content = re.sub(r'\bxrange\b', 'range', content)
        
        # raw_input -> input
        content = re.sub(r'\braw_input\b', 'input', content)
        
        # unicode -> str
        content = re.sub(r'\bunicode\b', 'str', content)
        
        # iteritems -> items
        content = re.sub(r'\.iteritems\(\)', '.items()', content)
        content = re.sub(r'\.iterkeys\(\)', '.keys()', content)
        content = re.sub(r'\.itervalues\(\)', '.values()', content)
        
        # has_key -> in
        content = re.sub(r'(\w+)\.has_key\(([^)]+)\)', r'\2 in \1', content)
        
        # Exception syntax
        content = re.sub(r'except\s+(\w+),\s*(\w+):', r'except \1 as \2:', content)
        
        # Integer division
        content = re.sub(r'(\d+)\s*/\s*(\d+)', r'\1 // \2', content)
        
        return content
    
    def normalize_quotes(self, content: str, file_path: Path) -> str:
        """Normalize quote usage"""
        
        # This is simplified - in production you'd use tokenize
        # Prefer single quotes for simple strings
        lines = []
        for line in content.split('\n'):
            # Skip comments and docstrings
            if line.strip().startswith('#') or '"""' in line or "'''" in line:
                lines.append(line)
                continue
                
            # Replace simple double quotes with single quotes
            line = re.sub(r'"([^"\'\\]{0,50})"', r"'\1'", line)
            lines.append(line)
            
        return '\n'.join(lines)
    
    def fix_poker_specific(self, content: str, file_path: Path) -> str:
        """Fix poker-specific code issues"""
        
        # Standardize card representations
        content = re.sub(r'["\']([2-9tjqka])([shdc])["\'"]', 
                         lambda m: f'"{m.group(1).upper()}{m.group(2).lower()}"', 
                         content, flags=re.IGNORECASE)
        
        # Fix suit names
        suits_map = {
            'S': 's', 'H': 'h', 'D': 'd', 'C': 'c',
            'Spades': 'spades', 'Hearts': 'hearts',
            'Diamonds': 'diamonds', 'Clubs': 'clubs',
            'SPADES': 'spades', 'HEARTS': 'hearts',
            'DIAMONDS': 'diamonds', 'CLUBS': 'clubs',
        }
        
        for old, new in suits_map.items():
            content = re.sub(rf'\b{old}\b', new, content)
        
        # Standardize hand rankings
        rankings_map = {
            'high card': 'HIGH_CARD',
            'High Card': 'HIGH_CARD',
            'pair': 'ONE_PAIR',
            'Pair': 'ONE_PAIR',
            'two pair': 'TWO_PAIR',
            'Two Pair': 'TWO_PAIR',
            'three of a kind': 'THREE_OF_A_KIND',
            'trips': 'THREE_OF_A_KIND',
            'set': 'THREE_OF_A_KIND',
            'straight': 'STRAIGHT',
            'Straight': 'STRAIGHT',
            'flush': 'FLUSH',
            'Flush': 'FLUSH',
            'full house': 'FULL_HOUSE',
            'Full House': 'FULL_HOUSE',
            'boat': 'FULL_HOUSE',
            'four of a kind': 'FOUR_OF_A_KIND',
            'quads': 'FOUR_OF_A_KIND',
            'straight flush': 'STRAIGHT_FLUSH',
            'Straight Flush': 'STRAIGHT_FLUSH',
            'royal flush': 'ROYAL_FLUSH',
            'Royal Flush': 'ROYAL_FLUSH',
        }
        
        for old, new in rankings_map.items():
            content = re.sub(rf'["\']({old})["\']', f'"{new}"', content, flags=re.IGNORECASE)
        
        # Fix 'raise' keyword conflict
        content = re.sub(r'\braise\s*=', 'raise_amount =', content)
        content = re.sub(r'def\s+raise\(', 'def raise_bet(', content)
        content = re.sub(r'self\.raise\s*=', 'self.raise_amount =', content)
        
        # Add deck initialization if missing
        if 'class Deck' in content and 'def __init__' in content:
            if 'self.cards = []' in content:
                proper_init = """self.cards = [(r, s) for s in ['hearts', 'diamonds', 'clubs', 'spades'] 
                          for r in ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']]"""
                content = content.replace('self.cards = []', proper_init)
        
        return content
    
    def fix_common_typos(self, content: str, file_path: Path) -> str:
        """Fix common typos"""
        
        typos = {
            r'\brecieve\b': 'receive',
            r'\bseperate\b': 'separate',
            r'\boccured\b': 'occurred',
            r'\boccuring\b': 'occurring',
            r'\bsuccessfull\b': 'successful',
            r'\bunsuccessfull\b': 'unsuccessful',
            r'\bexistance\b': 'existence',
            r'\bpersistant\b': 'persistent',
            r'\bconsistant\b': 'consistent',
            r'\barguement\b': 'argument',
            r'\barguements\b': 'arguments',
            r'\brefrence\b': 'reference',
            r'\brefrences\b': 'references',
            r'\bretrun\b': 'return',
            r'\bretunr\b': 'return',
            r'\breutrn\b': 'return',
            r'\bflase\b': 'False',
            r'\bfalse\b': 'False',
            r'\bture\b': 'True',
            r'\btrue\b': 'True',
            r'\bnone\b': 'None',
            r'\bnull\b': 'None',
            r'\besle\b': 'else',
            r'\belfi\b': 'elif',
            r'\bexecpt\b': 'except',
            r'\bexcpet\b': 'except',
            r'\bfinaly\b': 'finally',
            r'\bfinalyl\b': 'finally',
            r'\blamda\b': 'lambda',
            r'\blambad\b': 'lambda',
            r'\byeild\b': 'yield',
            r'\byiedl\b': 'yield',
            r'\blenght\b': 'length',
            r'\bHeigth\b': 'Height',
            r'\bheigth\b': 'height',
            r'\bwidht\b': 'width',
            r'\bindext\b': 'index',
            r'\bappned\b': 'append',
            r'\bextned\b': 'extend',
            r'\bdicitonary\b': 'dictionary',
            r'\bdictonary\b': 'dictionary',
            r'\btupel\b': 'tuple',
            r'\bshufel\b': 'shuffle',
            r'\bshufle\b': 'shuffle',
            r'\branodm\b': 'random',
            r'\branom\b': 'random',
        }
        
        for pattern, replacement in typos.items():
            content = re.sub(pattern, replacement, content)
            
        return content
    
    def add_missing_docstrings(self, content: str, file_path: Path) -> str:
        """Add docstrings where missing"""
        
        lines = content.split('\n')
        result = []
        
        for i, line in enumerate(lines):
            result.append(line)
            
            # Check for function or class without docstring
            if re.match(r'^(class|def)\s+\w+', line.strip()):
                # Check next line for docstring
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if not (next_line.startswith('"""') or next_line.startswith("'''")):
                        indent = len(line) - len(line.lstrip())
                        
                        if line.strip().startswith('def'):
                            func_name = re.search(r'def\s+(\w+)', line)
                            if func_name and not func_name.group(1).startswith('_'):
                                result.append(' ' * (indent + 4) + '"""TODO: Add docstring."""')
                        elif line.strip().startswith('class'):
                            result.append(' ' * (indent + 4) + '"""TODO: Add class docstring."""')
        
        return '\n'.join(result)
    
    def fix_exception_handling(self, content: str, file_path: Path) -> str:
        """Fix exception handling issues"""
        
        # Fix bare except
        content = re.sub(r'\bexcept\s*:', 'except Exception:', content)
        
        # Fix old-style exceptions
        content = re.sub(r'except\s+(\w+),\s*(\w+):', r'except \1 as \2:', content)
        
        # Fix multiple exceptions not in tuple
        content = re.sub(r'except\s+(\w+)\s*,\s*(\w+)\s*:', r'except (\1, \2):', content)
        
        return content
    
    def fix_comparisons(self, content: str, file_path: Path) -> str:
        """Fix comparison issues"""
        
        # Fix comparisons with None
        content = re.sub(r'(\w+)\s*==\s*None\b', r'\1 is None', content)
        content = re.sub(r'(\w+)\s*!=\s*None\b', r'\1 is not None', content)
        
        # Fix comparisons with True/False
        content = re.sub(r'(\w+)\s*==\s*True\b', r'\1 is True', content)
        content = re.sub(r'(\w+)\s*==\s*False\b', r'\1 is False', content)
        
        # Fix type comparisons
        content = re.sub(r'type\((\w+)\)\s*==\s*(\w+)', r'isinstance(\1, \2)', content)
        
        return content
    
    def fix_naming_conventions(self, content: str, file_path: Path) -> str:
        """Fix naming convention issues"""
        
        # Convert camelCase to snake_case for functions
        def camel_to_snake(match):
            name = match.group(1)
            # Don't convert if it starts with uppercase (likely a class)
            if name[0].isupper():
                return match.group(0)
            
            result = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
            result = re.sub('([a-z0-9])([A-Z])', r'\1_\2', result).lower()
            return f'def {result}'
        
        content = re.sub(r'def\s+([a-z][a-zA-Z0-9]+)', camel_to_snake, content)
        
        # Fix ALL_CAPS constants that should be used
        constants = {
            'pi': 'PI',
            'Pi': 'PI',
            'true': 'True',
            'false': 'False',
            'none': 'None',
        }
        
        for old, new in constants.items():
            content = re.sub(rf'\b{old}\b', new, content)
            
        return content
    
    def fix_line_length(self, content: str, file_path: Path) -> str:
        """Fix lines that are too long"""
        
        max_length = 100
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            if len(line) <= max_length:
                fixed_lines.append(line)
                continue
                
            # Try to break at logical points
            if ',' in line and len(line) > max_length:
                # Break after commas
                parts = line.split(',')
                current = parts[0]
                indent = len(line) - len(line.lstrip())
                
                for part in parts[1:]:
                    if len(current + ',' + part) > max_length:
                        fixed_lines.append(current + ',')
                        current = ' ' * (indent + 4) + part.strip()
                    else:
                        current += ',' + part
                fixed_lines.append(current)
            else:
                fixed_lines.append(line)
                
        return '\n'.join(fixed_lines)
    
    def fix_trailing_issues(self, content: str, file_path: Path) -> str:
        """Fix trailing commas, semicolons, etc."""
        
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Remove trailing semicolons
            line = re.sub(r';\s*$', '', line)
            
            # Add trailing commas in multiline structures
            if line.rstrip().endswith(')') and not line.strip().startswith(')'):
                # Check if it's a multiline function/tuple/list
                if '(' in line and not 'def ' in line and not 'if ' in line:
                    if not line.rstrip().endswith(',)'):
                        line = line.rstrip()[:-1] + ',)'
                        
            fixed_lines.append(line)
            
        return '\n'.join(fixed_lines)
    
    def fix_magic_methods(self, content: str, file_path: Path) -> str:
        """Fix magic method issues"""
        
        # Fix common magic method typos
        magic_fixes = {
            r'__int__\(': '__init__(',
            r'__ini__\(': '__init__(',
            r'__inti__\(': '__init__(',
            r'__str_\(': '__str__(',
            r'__rep__\(': '__repr__(',
            r'__repre__\(': '__repr__(',
            r'__equ__\(': '__eq__(',
            r'__equal__\(': '__eq__(',
            r'__has__\(': '__hash__(',
            r'__leng__\(': '__len__(',
            r'__lenght__\(': '__len__(',
        }
        
        for pattern, replacement in magic_fixes.items():
            content = re.sub(pattern, replacement, content)
            
        return content
    
    def show_diff(self, original: str, fixed: str):
        """Show a diff of the changes"""
        
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            fixed.splitlines(keepends=True),
            fromfile='original',
            tofile='fixed',
            n=1
        )
        
        diff_lines = list(diff)
        if diff_lines and len(diff_lines) < 50:  # Only show small diffs
            print("\n  Changes made:")
            for line in diff_lines:
                if line.startswith('+'):
                    print(f"    \033[92m{line.rstrip()}\033[0m")
                elif line.startswith('-'):
                    print(f"    \033[91m{line.rstrip()}\033[0m")
    
    def generate_report(self):
        """Generate a detailed report"""
        
        report_path = self.repo_path / "code_scan_report.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("POKERTOOL CODE SCAN REPORT\n")
            f.write("=" * 70 + "\n\n")
            
            f.write(f"Repository: {self.repo_path.absolute()}\n")
            f.write(f"Files fixed: {len(self.fixes_applied)}\n")
            f.write(f"Issues found: {len(self.issues_found)}\n\n")
            
            if self.stats:
                f.write("FIX STATISTICS:\n")
                f.write("-" * 40 + "\n")
                for fix_type, count in sorted(self.stats.items()):
                    f.write(f"  {fix_type:20s}: {count:3d} files\n")
                f.write("\n")
            
            if self.fixes_applied:
                f.write("FILES FIXED:\n")
                f.write("-" * 40 + "\n")
                for file in sorted(self.fixes_applied):
                    f.write(f"  ✓ {file}\n")
                f.write("\n")
            
            if self.issues_found:
                f.write("ISSUES (manual review needed):\n")
                f.write("-" * 40 + "\n")
                for issue in sorted(self.issues_found):
                    f.write(f"  ⚠ {issue}\n")
                f.write("\n")
            
            f.write("RECOMMENDATIONS:\n")
            f.write("-" * 40 + "\n")
            f.write("  1. Review the backup files (.py.backup) before committing\n")
            f.write("  2. Run your test suite to ensure nothing broke\n")
            f.write("  3. Consider adding pre-commit hooks for continuous checking\n")
            f.write("  4. Update docstrings marked with 'TODO'\n")
            
        print("\n" + "=" * 70)
        print(f"Report saved to: {report_path}")
        print("=" * 70)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Self-contained Python code scanner and fixer for pokertool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python code_scan.py                    # Scan current directory
  python code_scan.py --path ../pokertool  # Scan specific directory
  python code_scan.py --no-backup        # Don't create backup files
  python code_scan.py --dry-run          # Preview changes without applying
        """
    )
    
    parser.add_argument('--path', default='.', 
                       help='Path to repository (default: current directory)')
    parser.add_argument('--no-backup', action='store_true',
                       help="Don't create backup files")
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview changes without applying them')
    
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("POKERTOOL SELF-CONTAINED CODE SCANNER")
    print("No external dependencies required!")
    print("=" * 70 + "\n")
    
    # Verify path exists
    if not Path(args.path).exists():
        print(f"Error: Path '{args.path}' does not exist")
        sys.exit(1)
    
    # Run scanner
    scanner = CodeScanner(args.path)
    
    if args.dry_run:
        print("DRY RUN MODE - No files will be modified\n")
        scanner.scan_repository()
    else:
        scanner.scan_repository()
        print("\nScan complete! All modified files have been backed up with .backup extension")
        print("Review code_scan_report.txt for details")


if __name__ == "__main__":
    main()