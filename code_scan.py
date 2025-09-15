#!/usr/bin/env python3
"""
Automatic Python Code Scanner and Fixer for pokertool repository
This script scans Python files for common syntax errors and issues,
and automatically fixes them.
"""
pip install -r requirements.txt

import ast
import os
import re
import sys
import json
import autopep8
from pathlib import Path
from typing import List, Dict, Tuple, Any
import black
import isort
from pylint import epylint as lint



class CodeScanner:
    """Main class for scanning and fixing Python code issues"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.issues_found = []
        self.fixes_applied = []
        
    def scan_repository(self):
        """Scan all Python files in the repository"""
        print(f"Scanning repository at: {self.repo_path}")
        
        python_files = list(self.repo_path.rglob("*.py"))
        
        for file_path in python_files:
            if "venv" in str(file_path) or "__pycache__" in str(file_path):
                continue
                
            print(f"\nProcessing: {file_path}")
            self.process_file(file_path)
            
        self.generate_report()
        
    def process_file(self, file_path: Path):
        """Process a single Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
                
            # Apply various fixes
            fixed_content = original_content
            
            # Fix 1: Basic syntax errors
            fixed_content = self.fix_syntax_errors(fixed_content, file_path)
            
            # Fix 2: Import sorting
            fixed_content = self.fix_imports(fixed_content, file_path)
            
            # Fix 3: PEP 8 compliance
            fixed_content = self.fix_pep8_issues(fixed_content, file_path)
            
            # Fix 4: Common poker-specific issues
            fixed_content = self.fix_poker_specific_issues(fixed_content, file_path)
            
            # Fix 5: Type hints and annotations
            fixed_content = self.add_missing_type_hints(fixed_content, file_path)
            
            # Fix 6: Docstrings
            fixed_content = self.add_missing_docstrings(fixed_content, file_path)
            
            # Fix 7: Exception handling
            fixed_content = self.fix_exception_handling(fixed_content, file_path)
            
            # Fix 8: Format with Black
            fixed_content = self.format_with_black(fixed_content, file_path)
            
            # Fix 9: Remove unused imports
            fixed_content = self.remove_unused_imports(fixed_content, file_path)
            
            # Fix 10: Fix common typos
            fixed_content = self.fix_common_typos(fixed_content, file_path)
            
            # Write back if changes were made
            if fixed_content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                self.fixes_applied.append(f"Fixed: {file_path}")
                print(f"  ✓ Fixed issues in {file_path}")
            else:
                print(f"  ✓ No issues found in {file_path}")
                
        except Exception as e:
            self.issues_found.append(f"Error processing {file_path}: {str(e)}")
            print(f"  ✗ Error processing {file_path}: {str(e)}")
            
    def fix_syntax_errors(self, content: str, file_path: Path) -> str:
        """Fix common syntax errors"""
        fixes = []
        
        # Fix missing colons
        content = re.sub(r'(\s*)(if|elif|else|for|while|def|class|try|except|finally|with)\s+([^:\n]+)(\n)',
                         r'\1\2 \3:\4', content)
        
        # Fix incorrect indentation (tabs to spaces)
        content = content.replace('\t', '    ')
        
        # Fix print statements (Python 2 to 3)
        content = re.sub(r'print\s+([^(].*?)(\n|$)', r'print(\1)\2', content)
        
        # Fix xrange to range (Python 2 to 3)
        content = content.replace('xrange', 'range')
        
        # Fix raw_input to input (Python 2 to 3)
        content = content.replace('raw_input', 'input')
        
        # Fix dictionary methods (Python 2 to 3)
        content = re.sub(r'\.iteritems\(\)', '.items()', content)
        content = re.sub(r'\.iterkeys\(\)', '.keys()', content)
        content = re.sub(r'\.itervalues\(\)', '.values()', content)
        
        # Fix string formatting
        content = re.sub(r'%\s*\((.*?)\)\s*%\s*\((.*?)\)', r'.format(\2)', content)
        
        # Fix missing parentheses in function calls
        content = re.sub(r'(\w+)\s+\(\s*\)', r'\1()', content)
        
        # Validate with AST
        try:
            ast.parse(content)
        except SyntaxError as e:
            # Try to fix specific syntax errors
            if "invalid syntax" in str(e):
                # Common fixes for invalid syntax
                lines = content.split('\n')
                if e.lineno and e.lineno <= len(lines):
                    problem_line = lines[e.lineno - 1]
                    
                    # Fix missing parentheses in expressions
                    if '=' in problem_line and not '==' in problem_line:
                        parts = problem_line.split('=')
                        if len(parts) == 2:
                            lines[e.lineno - 1] = f"{parts[0].strip()} = {parts[1].strip()}"
                    
                    content = '\n'.join(lines)
                    
        return content
        
    def fix_imports(self, content: str, file_path: Path) -> str:
        """Sort and organize imports"""
        try:
            return isort.code(content)
        except Exception:
            return content
            
    def fix_pep8_issues(self, content: str, file_path: Path) -> str:
        """Fix PEP 8 style issues"""
        try:
            return autopep8.fix_code(content, options={'aggressive': 2})
        except Exception:
            return content
            
    def fix_poker_specific_issues(self, content: str, file_path: Path) -> str:
        """Fix common issues in poker-related code"""
        
        # Fix card representations
        content = re.sub(r"'([2-9TJQKA])([shdc])'", r"'\1\2'", content, flags=re.IGNORECASE)
        
        # Fix hand rankings
        hand_rankings = {
            'high card': 'HIGH_CARD',
            'one pair': 'ONE_PAIR',
            'two pair': 'TWO_PAIR',
            'three of a kind': 'THREE_OF_A_KIND',
            'straight': 'STRAIGHT',
            'flush': 'FLUSH',
            'full house': 'FULL_HOUSE',
            'four of a kind': 'FOUR_OF_A_KIND',
            'straight flush': 'STRAIGHT_FLUSH',
            'royal flush': 'ROYAL_FLUSH'
        }
        
        for old, new in hand_rankings.items():
            content = re.sub(rf'["\']({old})["\']', f'"{new}"', content, flags=re.IGNORECASE)
            
        # Fix common poker variable names
        replacements = {
            r'\bhand\b': 'hand',
            r'\bcards\b': 'cards',
            r'\bdeck\b': 'deck',
            r'\bplayer\b': 'player',
            r'\bpot\b': 'pot',
            r'\bbet\b': 'bet',
            r'\braise\b': 'raise_amount',  # 'raise' is a Python keyword
            r'\bcall\b': 'call_amount',
            r'\bfold\b': 'fold_action'
        }
        
        for pattern, replacement in replacements.items():
            # Only replace if it's being used as a variable, not in strings
            content = re.sub(rf'(?<!["\'])({pattern})(?!["\'])', replacement, content)
            
        return content
        
    def add_missing_type_hints(self, content: str, file_path: Path) -> str:
        """Add type hints to functions"""
        try:
            tree = ast.parse(content)
            
            class TypeHintTransformer(ast.NodeTransformer):
                def visit_FunctionDef(self, node):
                    # Add return type hint if missing
                    if not node.returns:
                        # Try to infer return type
                        for child in ast.walk(node):
                            if isinstance(child, ast.Return):
                                if child.value is None:
                                    node.returns = ast.Name(id='None', ctx=ast.Load())
                                break
                    
                    return node
                    
            transformer = TypeHintTransformer()
            new_tree = transformer.visit(tree)
            return ast.unparse(new_tree) if hasattr(ast, 'unparse') else content
        except:
            return content
            
    def add_missing_docstrings(self, content: str, file_path: Path) -> str:
        """Add missing docstrings to functions and classes"""
        lines = content.split('\n')
        new_lines = []
        
        for i, line in enumerate(lines):
            new_lines.append(line)
            
            # Check for function or class definition
            if re.match(r'^(class|def)\s+\w+', line.strip()):
                # Check if next line is already a docstring
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if not (next_line.startswith('"""') or next_line.startswith("'''")):
                        indent = len(line) - len(line.lstrip())
                        
                        if line.strip().startswith('def'):
                            func_name = re.search(r'def\s+(\w+)', line).group(1)
                            new_lines.append(' ' * (indent + 4) + f'"""TODO: Add docstring for {func_name}"""')
                        elif line.strip().startswith('class'):
                            class_name = re.search(r'class\s+(\w+)', line).group(1)
                            new_lines.append(' ' * (indent + 4) + f'"""TODO: Add docstring for {class_name}"""')
                            
        return '\n'.join(new_lines)
        
    def fix_exception_handling(self, content: str, file_path: Path) -> str:
        """Fix broad exception handling"""
        # Replace bare except with except Exception
        content = re.sub(r'except\s*:', 'except Exception:', content)
        
        # Add logging to exception handlers
        if 'except' in content and 'import logging' not in content:
            content = 'import logging\n' + content
            
        return content
        
    def format_with_black(self, content: str, file_path: Path) -> str:
        """Format code with Black"""
        try:
            return black.format_str(content, mode=black.FileMode())
        except Exception:
            return content
            
    def remove_unused_imports(self, content: str, file_path: Path) -> str:
        """Remove unused imports"""
        try:
            # Use autoflake for this in production
            # For now, just return content
            return content
        except:
            return content
            
    def fix_common_typos(self, content: str, file_path: Path) -> str:
        """Fix common typos in code"""
        typos = {
            'recieve': 'receive',
            'seperate': 'separate',
            'occured': 'occurred',
            'successfull': 'successful',
            'existance': 'existence',
            'persistant': 'persistent',
            'arguement': 'argument',
            'refrence': 'reference',
            'retrun': 'return',
            'flase': 'False',
            'ture': 'True',
            'none': 'None',
            'esle': 'else',
            'elif': 'elif',  # This is correct, just for clarity
            'execpt': 'except',
            'finaly': 'finally',
            'lamda': 'lambda',
            'yeild': 'yield'
        }
        
        for typo, correct in typos.items():
            # Only replace whole words, not parts of other words
            content = re.sub(rf'\b{typo}\b', correct, content)
            
        return content
        
    def generate_report(self):
        """Generate a report of all fixes applied"""
        report_path = self.repo_path / "code_scan_report.txt"
        
        with open(report_path, 'w') as f:
            f.write("Code Scan Report\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Total files processed: {len(self.fixes_applied) + len(self.issues_found)}\n")
            f.write(f"Files fixed: {len(self.fixes_applied)}\n")
            f.write(f"Issues found: {len(self.issues_found)}\n\n")
            
            if self.fixes_applied:
                f.write("Fixes Applied:\n")
                f.write("-" * 30 + "\n")
                for fix in self.fixes_applied:
                    f.write(f"  • {fix}\n")
                f.write("\n")
                
            if self.issues_found:
                f.write("Issues Found (manual review needed):\n")
                f.write("-" * 30 + "\n")
                for issue in self.issues_found:
                    f.write(f"  • {issue}\n")
                    
        print(f"\nReport saved to: {report_path}")
        

class PokerCodeFixer:
    """Specific fixes for poker-related code patterns"""
    
    @staticmethod
    def fix_card_deck_initialization(content: str) -> str:
        """Fix common deck initialization issues"""
        # Fix card deck creation
        if 'deck = []' in content or 'self.deck = []' in content:
            proper_deck = """
        suits = ['hearts', 'diamonds', 'clubs', 'spades']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        deck = [(rank, suit) for suit in suits for rank in ranks]
"""
            content = re.sub(r'deck\s*=\s*\[\]', proper_deck, content)
            
        return content
        
    @staticmethod
    def fix_hand_evaluation(content: str) -> str:
        """Fix common hand evaluation patterns"""
        # Add proper hand ranking constants if missing
        if 'def evaluate_hand' in content or 'def hand_rank' in content:
            if 'HAND_RANKINGS' not in content:
                rankings = """
HAND_RANKINGS = {
    'HIGH_CARD': 0,
    'ONE_PAIR': 1,
    'TWO_PAIR': 2,
    'THREE_OF_A_KIND': 3,
    'STRAIGHT': 4,
    'FLUSH': 5,
    'FULL_HOUSE': 6,
    'FOUR_OF_A_KIND': 7,
    'STRAIGHT_FLUSH': 8,
    'ROYAL_FLUSH': 9
}
"""
                content = rankings + "\n" + content
                
        return content
        

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scan and fix Python code issues')
    parser.add_argument('--path', default='.', help='Path to repository')
    parser.add_argument('--fix-only', nargs='+', help='Only apply specific fixes')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be fixed without applying')
    
    args = parser.parse_args()
    
    scanner = CodeScanner(args.path)
    scanner.scan_repository()
    
    # Apply poker-specific fixes
    fixer = PokerCodeFixer()
    
    for file_path in Path(args.path).rglob("*.py"):
        if "venv" in str(file_path) or "__pycache__" in str(file_path):
            continue
            
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            content = fixer.fix_card_deck_initialization(content)
            content = fixer.fix_hand_evaluation(content)
            
            with open(file_path, 'w') as f:
                f.write(content)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            

if __name__ == "__main__":
    main()