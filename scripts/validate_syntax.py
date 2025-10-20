#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PokerTool Syntax Validation Script
===================================

Comprehensive Python syntax checker for all modules in the PokerTool repository.
Validates syntax, imports, and basic structure.

Usage:
    python scripts/validate_syntax.py
    python scripts/validate_syntax.py --verbose
    python scripts/validate_syntax.py --fix

Author: PokerTool Development Team
Version: 1.0.0
"""

import sys
import os
import py_compile
import tempfile
from pathlib import Path
from typing import List, Tuple
import argparse

# ANSI color codes
class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color
    BOLD = '\033[1m'

class SyntaxValidator:
    """Validates Python syntax across the repository."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.errors = []
        
    def check_file(self, filepath: Path) -> Tuple[bool, str]:
        """
        Check syntax of a single Python file.
        
        Returns:
            Tuple of (success, error_message)
        """
        self.total += 1
        
        try:
            # Use py_compile to check syntax
            with tempfile.NamedTemporaryFile(suffix='.pyc', delete=True) as tmp:
                py_compile.compile(str(filepath), cfile=tmp.name, doraise=True)
            
            # Additional checks
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Check for common issues
                issues = []
                
                # Check for __future__ imports not at beginning
                lines = content.split('\n')
                first_code_line = -1
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    
                    # Skip shebang, encoding, empty lines, comments
                    if not stripped or stripped.startswith('#'):
                        continue
                    
                    # Skip docstrings
                    if stripped.startswith('"""') or stripped.startswith("'''"):
                        continue
                    
                    # Check for __future__
                    if 'from __future__ import' in line:
                        if first_code_line != -1 and first_code_line < i:
                            issues.append(f"Line {i+1}: __future__ import not at beginning")
                    elif stripped.startswith(('import ', 'from ')):
                        if first_code_line == -1:
                            first_code_line = i
                    elif stripped.startswith('__'):
                        if first_code_line == -1:
                            first_code_line = i
                
                if issues:
                    self.failed += 1
                    error_msg = '; '.join(issues)
                    self.errors.append((filepath, error_msg))
                    return False, error_msg
            
            self.passed += 1
            return True, ""
            
        except py_compile.PyCompileError as e:
            self.failed += 1
            error_msg = str(e)
            self.errors.append((filepath, error_msg))
            return False, error_msg
        except Exception as e:
            self.failed += 1
            error_msg = f"Unexpected error: {str(e)}"
            self.errors.append((filepath, error_msg))
            return False, error_msg
    
    def check_directory(self, directory: Path, pattern: str = "*.py") -> None:
        """Check all Python files in a directory."""
        files = sorted(directory.rglob(pattern))
        
        # Exclude backup files and __pycache__
        files = [f for f in files if not any(
            part.startswith('.') or part == '__pycache__' or part.endswith('.bak')
            for part in f.parts
        )]
        
        for filepath in files:
            success, error = self.check_file(filepath)
            
            if success:
                print(f"{Colors.GREEN}✓{Colors.NC} {filepath}")
                if self.verbose:
                    print(f"  {Colors.BLUE}Status: VALID{Colors.NC}")
            else:
                print(f"{Colors.RED}✗{Colors.NC} {filepath}")
                if self.verbose or True:  # Always show errors
                    print(f"  {Colors.RED}Error: {error}{Colors.NC}")
    
    def print_summary(self) -> int:
        """Print validation summary and return exit code."""
        print("\n" + "="*60)
        print(f"{Colors.BOLD}VALIDATION SUMMARY{Colors.NC}")
        print("="*60)
        print(f"Total files checked: {self.total}")
        print(f"Passed: {Colors.GREEN}{self.passed}{Colors.NC}")
        print(f"Failed: {Colors.RED}{self.failed}{Colors.NC}")
        
        if self.failed == 0:
            print(f"\n{Colors.GREEN}✓ All files passed syntax validation!{Colors.NC}\n")
            return 0
        else:
            print(f"\n{Colors.RED}✗ {self.failed} file(s) failed syntax validation{Colors.NC}")
            print("\nFailed files:")
            for filepath, error in self.errors:
                print(f"  {Colors.RED}•{Colors.NC} {filepath}")
                if self.verbose:
                    print(f"    {error}")
            print()
            return 1

def main():
    parser = argparse.ArgumentParser(
        description='Validate Python syntax across PokerTool repository'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show verbose output'
    )
    parser.add_argument(
        '--path', '-p',
        type=str,
        default='.',
        help='Path to check (default: current directory)'
    )
    parser.add_argument(
        '--pattern',
        type=str,
        default='*.py',
        help='File pattern to match (default: *.py)'
    )
    
    args = parser.parse_args()
    
    print("╔════════════════════════════════════════════════════════════╗")
    print("║     PokerTool Syntax Validation                           ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    
    validator = SyntaxValidator(verbose=args.verbose)
    
    # Check main source directory
    print(f"{Colors.BOLD}📝 Checking source files...{Colors.NC}")
    print("─" * 60)
    src_path = Path(args.path) / 'src' / 'pokertool'
    if src_path.exists():
        validator.check_directory(src_path, '*.py')
    else:
        print(f"{Colors.YELLOW}⚠ Source directory not found: {src_path}{Colors.NC}")
    
    print()
    
    # Check test files
    print(f"{Colors.BOLD}🧪 Checking test files...{Colors.NC}")
    print("─" * 60)
    tests_path = Path(args.path) / 'tests'
    if tests_path.exists():
        validator.check_directory(tests_path, 'test_*.py')
    else:
        print(f"{Colors.YELLOW}⚠ Tests directory not found: {tests_path}{Colors.NC}")
    
    print()
    
    # Check root level files
    print(f"{Colors.BOLD}📦 Checking root level files...{Colors.NC}")
    print("─" * 60)
    root_files = [
        'start.py',
        'run_tests.py'
    ]
    
    for filename in root_files:
        filepath = Path(args.path) / filename
        if filepath.exists():
            success, error = validator.check_file(filepath)
            if success:
                print(f"{Colors.GREEN}✓{Colors.NC} {filepath}")
            else:
                print(f"{Colors.RED}✗{Colors.NC} {filepath}")
                print(f"  {Colors.RED}Error: {error}{Colors.NC}")
    
    # Print summary
    exit_code = validator.print_summary()
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
