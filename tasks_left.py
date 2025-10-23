#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PokerTool TODO Task Viewer
===========================

This script displays all remaining tasks from docs/TODO.md with color-coded
priorities to help visualize what work is left to do.

Usage:
    # Show all remaining tasks
    python tasks_left.py
    
    # Show only high priority tasks (P0, P1)
    python tasks_left.py --high-priority
    
    # Show tasks by section
    python tasks_left.py --by-section
    
    # Show summary statistics
    python tasks_left.py --summary

Color Coding:
    - High Priority (P0, P1): Yellow
    - Medium Priority (P2): Green  
    - Low Priority (P3): Blue

Author: PokerTool Development Team
Version: 1.0.0
"""

import re
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict


class Colors:
    """ANSI color codes for terminal output."""
    # Priority colors
    HIGH = '\033[93m'      # Yellow for P0/P1 (high priority)
    MEDIUM = '\033[92m'    # Green for P2 (medium priority)
    LOW = '\033[94m'       # Blue for P3 (low priority)
    
    # Other colors
    HEADER = '\033[95m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    ENDC = '\033[0m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    DIM = '\033[2m'


class Task:
    """Represents a single TODO task."""
    
    def __init__(self, line: str, line_number: int):
        """
        Parse a TODO task line.
        
        Args:
            line: The task line from TODO.md
            line_number: Line number in the file
        """
        self.line = line
        self.line_number = line_number
        self.completed = False
        self.priority = "P3"
        self.effort = "M"
        self.title = ""
        self.description = ""
        
        self._parse()
    
    def _parse(self):
        """Parse the task line to extract components."""
        # Match pattern: - [x] [P0][M] Title — description
        match = re.match(
            r'^- \[([ x])\]\s*\[([P\d]+)\]\[([SML])\]\s*(.+?)(?:\s*—\s*(.+))?$',
            self.line.strip()
        )
        
        if match:
            checkbox, priority, effort, title, description = match.groups()
            self.completed = checkbox.lower() == 'x'
            self.priority = priority
            self.effort = effort
            self.title = title.strip()
            self.description = description.strip() if description else ""
    
    def get_color(self) -> str:
        """Get color based on priority."""
        if self.priority in ['P0', 'P1']:
            return Colors.HIGH  # Yellow for high priority
        elif self.priority == 'P2':
            return Colors.MEDIUM  # Green for medium priority
        else:  # P3
            return Colors.LOW  # Blue for low priority
    
    def get_priority_label(self) -> str:
        """Get priority label with emoji."""
        labels = {
            'P0': '🔴 CRITICAL',
            'P1': '🟡 HIGH',
            'P2': '🟢 MEDIUM',
            'P3': '🔵 LOW'
        }
        return labels.get(self.priority, '⚪ UNKNOWN')
    
    def get_effort_label(self) -> str:
        """Get effort label."""
        labels = {
            'S': 'Small (<1 day)',
            'M': 'Medium (1-3 days)',
            'L': 'Large (>3 days)'
        }
        return labels.get(self.effort, 'Unknown')
    
    def __str__(self) -> str:
        """Format task for display."""
        color = self.get_color()
        
        # Format: [P0][M] Title
        task_header = f"{color}{Colors.BOLD}[{self.priority}][{self.effort}]{Colors.ENDC} {color}{self.title}{Colors.ENDC}"
        
        if self.description:
            task_desc = f"{Colors.DIM}    → {self.description}{Colors.ENDC}"
            return f"{task_header}\n{task_desc}"
        
        return task_header


class TODOViewer:
    """Parses and displays TODO.md tasks."""
    
    def __init__(self, todo_path: Path = None):
        """
        Initialize TODO viewer.
        
        Args:
            todo_path: Path to TODO.md file (default: docs/TODO.md)
        """
        if todo_path is None:
            todo_path = Path(__file__).parent / 'docs' / 'TODO.md'
        
        self.todo_path = todo_path
        self.tasks: List[Task] = []
        self.sections: Dict[str, List[Task]] = defaultdict(list)
        self.current_section = "General"
        
        self._load_tasks()
    
    def _load_tasks(self):
        """Load and parse tasks from TODO.md."""
        if not self.todo_path.exists():
            raise FileNotFoundError(f"TODO.md not found at {self.todo_path}")
        
        with open(self.todo_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines, 1):
            # Track sections (lines starting with ##)
            if line.strip().startswith('##'):
                self.current_section = line.strip().lstrip('#').strip()
                continue
            
            # Match task lines
            if re.match(r'^- \[[ x]\]', line.strip()):
                task = Task(line, i)
                self.tasks.append(task)
                self.sections[self.current_section].append(task)
    
    def get_remaining_tasks(self, priority_filter: List[str] = None) -> List[Task]:
        """
        Get all remaining (uncompleted) tasks.
        
        Args:
            priority_filter: Optional list of priorities to filter (e.g., ['P0', 'P1'])
        
        Returns:
            List of remaining tasks
        """
        remaining = [t for t in self.tasks if not t.completed]
        
        if priority_filter:
            remaining = [t for t in remaining if t.priority in priority_filter]
        
        return remaining
    
    def get_statistics(self) -> Dict[str, any]:
        """Calculate task statistics."""
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t.completed)
        remaining = total - completed
        
        # Count by priority
        remaining_by_priority = defaultdict(int)
        for task in self.tasks:
            if not task.completed:
                remaining_by_priority[task.priority] += 1
        
        # Count by effort
        remaining_by_effort = defaultdict(int)
        for task in self.tasks:
            if not task.completed:
                remaining_by_effort[task.effort] += 1
        
        return {
            'total': total,
            'completed': completed,
            'remaining': remaining,
            'completion_rate': (completed / total * 100) if total > 0 else 0,
            'by_priority': dict(remaining_by_priority),
            'by_effort': dict(remaining_by_effort)
        }
    
    def display_summary(self):
        """Display summary statistics."""
        stats = self.get_statistics()
        
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}  PokerTool TODO Summary{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")
        
        # Overall stats
        print(f"{Colors.CYAN}Total Tasks:{Colors.ENDC} {stats['total']}")
        print(f"{Colors.CYAN}Completed:{Colors.ENDC} {stats['completed']}")
        print(f"{Colors.CYAN}Remaining:{Colors.ENDC} {stats['remaining']}")
        print(f"{Colors.CYAN}Completion Rate:{Colors.ENDC} {stats['completion_rate']:.1f}%")
        
        # Progress bar
        progress_width = 50
        filled = int(progress_width * stats['completed'] / stats['total']) if stats['total'] > 0 else 0
        bar = '█' * filled + '░' * (progress_width - filled)
        print(f"{Colors.CYAN}Progress:{Colors.ENDC} [{bar}] {stats['completion_rate']:.1f}%\n")
        
        # By priority
        print(f"{Colors.BOLD}Remaining by Priority:{Colors.ENDC}")
        for priority in ['P0', 'P1', 'P2', 'P3']:
            count = stats['by_priority'].get(priority, 0)
            if count > 0:
                color = Colors.HIGH if priority in ['P0', 'P1'] else Colors.MEDIUM if priority == 'P2' else Colors.LOW
                label = {
                    'P0': '🔴 CRITICAL',
                    'P1': '🟡 HIGH',
                    'P2': '🟢 MEDIUM',
                    'P3': '🔵 LOW'
                }.get(priority, priority)
                print(f"  {color}{label}:{Colors.ENDC} {count} tasks")
        
        # By effort
        print(f"\n{Colors.BOLD}Remaining by Effort:{Colors.ENDC}")
        for effort in ['S', 'M', 'L']:
            count = stats['by_effort'].get(effort, 0)
            if count > 0:
                label = {
                    'S': 'Small (<1 day)',
                    'M': 'Medium (1-3 days)',
                    'L': 'Large (>3 days)'
                }.get(effort, effort)
                print(f"  {label}: {count} tasks")
        
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")
    
    def display_tasks(self, by_section: bool = False, priority_filter: List[str] = None):
        """
        Display remaining tasks.
        
        Args:
            by_section: Group tasks by section
            priority_filter: Optional list of priorities to show
        """
        remaining = self.get_remaining_tasks(priority_filter)
        
        if not remaining:
            print(f"\n{Colors.BOLD}{Colors.MEDIUM}🎉 No remaining tasks! All work is complete!{Colors.ENDC}\n")
            return
        
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}  PokerTool Remaining Tasks ({len(remaining)}){Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")
        
        if by_section:
            self._display_by_section(remaining)
        else:
            self._display_flat(remaining)
    
    def _display_flat(self, tasks: List[Task]):
        """Display tasks as flat list."""
        # Group by priority for better organization
        by_priority = defaultdict(list)
        for task in tasks:
            by_priority[task.priority].append(task)
        
        # Display in priority order
        for priority in ['P0', 'P1', 'P2', 'P3']:
            if priority not in by_priority:
                continue
            
            priority_tasks = by_priority[priority]
            color = Colors.HIGH if priority in ['P0', 'P1'] else Colors.MEDIUM if priority == 'P2' else Colors.LOW
            
            label = {
                'P0': '🔴 CRITICAL PRIORITY',
                'P1': '🟡 HIGH PRIORITY',
                'P2': '🟢 MEDIUM PRIORITY',
                'P3': '🔵 LOW PRIORITY'
            }.get(priority, priority)
            
            print(f"{color}{Colors.BOLD}{label}{Colors.ENDC} ({len(priority_tasks)} tasks)\n")
            
            for task in priority_tasks:
                print(f"{task}\n")
            
            print()
    
    def _display_by_section(self, tasks: List[Task]):
        """Display tasks grouped by section."""
        # Create section mapping for remaining tasks
        remaining_sections = defaultdict(list)
        
        for section, section_tasks in self.sections.items():
            remaining_in_section = [t for t in section_tasks if not t.completed and t in tasks]
            if remaining_in_section:
                remaining_sections[section] = remaining_in_section
        
        # Display each section
        for section, section_tasks in remaining_sections.items():
            print(f"{Colors.CYAN}{Colors.BOLD}{'─'*70}{Colors.ENDC}")
            print(f"{Colors.CYAN}{Colors.BOLD}📂 {section}{Colors.ENDC} ({len(section_tasks)} tasks)\n")
            
            for task in section_tasks:
                print(f"{task}\n")
            
            print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="View remaining tasks from PokerTool TODO.md",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show all remaining tasks
  python tasks_left.py
  
  # Show only high priority tasks
  python tasks_left.py --high-priority
  
  # Show tasks grouped by section
  python tasks_left.py --by-section
  
  # Show summary only
  python tasks_left.py --summary
  
  # Show high priority tasks by section
  python tasks_left.py --high-priority --by-section

Color Legend:
  🔴 P0 (Critical) / 🟡 P1 (High) - Yellow
  🟢 P2 (Medium) - Green
  🔵 P3 (Low) - Blue
        """
    )
    
    parser.add_argument(
        '-s', '--summary',
        action='store_true',
        help='Show summary statistics only'
    )
    
    parser.add_argument(
        '-b', '--by-section',
        action='store_true',
        help='Group tasks by section'
    )
    
    parser.add_argument(
        '-H', '--high-priority',
        action='store_true',
        help='Show only high priority tasks (P0, P1)'
    )
    
    parser.add_argument(
        '-p', '--priority',
        choices=['P0', 'P1', 'P2', 'P3'],
        help='Show only tasks with specific priority'
    )
    
    args = parser.parse_args()
    
    try:
        # Load TODO viewer
        viewer = TODOViewer()
        
        # Determine priority filter
        priority_filter = None
        if args.high_priority:
            priority_filter = ['P0', 'P1']
        elif args.priority:
            priority_filter = [args.priority]
        
        # Display summary
        viewer.display_summary()
        
        # Display tasks if not summary-only
        if not args.summary:
            viewer.display_tasks(
                by_section=args.by_section,
                priority_filter=priority_filter
            )
        
        # Show tips
        print(f"{Colors.DIM}💡 Tip: Use --high-priority to focus on urgent tasks{Colors.ENDC}")
        print(f"{Colors.DIM}💡 Tip: Use --by-section to organize by feature area{Colors.ENDC}\n")
        
    except FileNotFoundError as e:
        print(f"{Colors.HIGH}Error: {str(e)}{Colors.ENDC}")
        return 1
    except Exception as e:
        print(f"{Colors.HIGH}Error: {str(e)}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
