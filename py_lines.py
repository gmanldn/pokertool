#!/usr/bin/env python3
"""
Script to count lines in all Python files and write results to lines.txt
"""

import os
from pathlib import Path


def count_lines_in_file(file_path):
    """Count the number of lines in a file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return 0


def find_python_files(directory):
    """Find all Python files in directory and subdirectories."""
    python_files = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                python_files.append(file_path)
    
    return sorted(python_files)


def main():
    """Main function to count lines and write to lines.txt"""
    # Get current directory
    current_dir = Path.cwd()
    
    # Find all Python files
    print("Finding Python files...")
    python_files = find_python_files(current_dir)
    
    # Clear and write to lines.txt
    with open('lines.txt', 'w', encoding='utf-8') as output_file:
        total_lines = 0
        
        print(f"Processing {len(python_files)} Python files...")
        
        for file_path in python_files:
            # Make path relative to current directory
            relative_path = os.path.relpath(file_path, current_dir)
            line_count = count_lines_in_file(file_path)
            
            # Write to file
            output_file.write(f"{line_count:8d} {relative_path}\n")
            total_lines += line_count
            
            # Progress indicator
            if len(python_files) > 100 and python_files.index(file_path) % 100 == 0:
                print(f"Processed {python_files.index(file_path)} files...")
        
        # Write total
        output_file.write(f"{total_lines:8d} total\n")
    
    print(f"Complete! Found {len(python_files)} Python files with {total_lines:,} total lines.")
    print("Results written to lines.txt")


if __name__ == "__main__":
    main()
