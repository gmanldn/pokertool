"""
TODO.md Parser Module

Parses markdown TODO files with checkboxes, priorities, effort estimates,
and nested tasks. Supports the PokerTool TODO.md format:

Format: - [ ] [P#][E#] Title — description. `file_path`

Where:
- P#: Priority (P0=critical, P1=high, P2=medium, P3=low)
- E#: Effort (S=<1 day, M=1-3 days, L=>3 days)
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
from enum import Enum
from pathlib import Path


class Priority(Enum):
    """Task priority levels"""
    P0 = 0  # Critical
    P1 = 1  # High
    P2 = 2  # Medium
    P3 = 3  # Low


class Effort(Enum):
    """Task effort estimates"""
    S = "small"      # < 1 day
    M = "medium"     # 1-3 days
    L = "large"      # > 3 days


@dataclass
class Task:
    """Represents a single task from TODO.md"""
    title: str
    description: str
    priority: Priority
    effort: Effort
    file_path: Optional[str]
    completed: bool
    line_number: int
    raw_line: str
    section: str = ""
    subsection: str = ""

    def __repr__(self) -> str:
        status = "✓" if self.completed else " "
        return f"[{status}] [{self.priority.name}][{self.effort.name}] {self.title}"


class TodoParser:
    """Parser for TODO.md markdown files"""

    # Regex patterns
    TASK_PATTERN = re.compile(
        r'^-\s+\[([ xX✓])\]\s+'  # Checkbox: - [ ] or - [x]
        r'\[P([0-3])\]'           # Priority: [P0] to [P3]
        r'\[([SML])\]'            # Effort: [S], [M], or [L]
        r'\s+(.+?)(?:\s+—\s+(.+?))?'  # Title — Description (optional)
        r'(?:\s+`([^`]+)`)?$'     # File path in backticks (optional)
    )

    SECTION_PATTERN = re.compile(r'^##\s+(.+)$')
    SUBSECTION_PATTERN = re.compile(r'^###\s+(.+)$')

    def __init__(self, todo_file: str = "docs/TODO.md"):
        """
        Initialize parser with path to TODO.md

        Args:
            todo_file: Path to TODO.md file relative to project root
        """
        self.todo_file = Path(todo_file)
        self.tasks: List[Task] = []
        self.current_section = ""
        self.current_subsection = ""

    def parse(self) -> List[Task]:
        """
        Parse TODO.md file and extract all tasks

        Returns:
            List of Task objects
        """
        if not self.todo_file.exists():
            raise FileNotFoundError(f"TODO file not found: {self.todo_file}")

        self.tasks = []
        self.current_section = ""
        self.current_subsection = ""

        with open(self.todo_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, start=1):
                line = line.rstrip()

                # Track sections
                section_match = self.SECTION_PATTERN.match(line)
                if section_match:
                    self.current_section = section_match.group(1)
                    self.current_subsection = ""
                    continue

                # Track subsections
                subsection_match = self.SUBSECTION_PATTERN.match(line)
                if subsection_match:
                    self.current_subsection = subsection_match.group(1)
                    continue

                # Parse task
                task_match = self.TASK_PATTERN.match(line)
                if task_match:
                    task = self._parse_task(task_match, line_num, line)
                    if task:
                        self.tasks.append(task)

        return self.tasks

    def _parse_task(self, match: re.Match, line_num: int, raw_line: str) -> Optional[Task]:
        """Parse a single task from regex match"""
        try:
            completed = match.group(1).lower() in ['x', '✓']
            priority_num = int(match.group(2))
            effort_char = match.group(3)
            title = match.group(4).strip()
            description = match.group(5).strip() if match.group(5) else ""
            file_path = match.group(6) if match.group(6) else None

            return Task(
                title=title,
                description=description,
                priority=Priority(priority_num),
                effort=Effort[effort_char],
                file_path=file_path,
                completed=completed,
                line_number=line_num,
                raw_line=raw_line,
                section=self.current_section,
                subsection=self.current_subsection
            )
        except (ValueError, KeyError) as e:
            # Invalid task format, skip
            return None

    def get_tasks_by_priority(self, priority: Priority) -> List[Task]:
        """Get all tasks with specified priority"""
        return [t for t in self.tasks if t.priority == priority]

    def get_incomplete_tasks(self) -> List[Task]:
        """Get all incomplete tasks"""
        return [t for t in self.tasks if not t.completed]

    def get_completed_tasks(self) -> List[Task]:
        """Get all completed tasks"""
        return [t for t in self.tasks if t.completed]

    def get_top_n_tasks(self, n: int = 20) -> List[Task]:
        """
        Get top N incomplete tasks (from start of file)

        Args:
            n: Number of tasks to return

        Returns:
            List of first N incomplete tasks
        """
        incomplete = self.get_incomplete_tasks()
        return incomplete[:n]

    def get_bottom_n_tasks(self, n: int = 20) -> List[Task]:
        """
        Get bottom N incomplete tasks (from end of file)

        Args:
            n: Number of tasks to return

        Returns:
            List of last N incomplete tasks
        """
        incomplete = self.get_incomplete_tasks()
        return incomplete[-n:] if len(incomplete) >= n else incomplete

    def get_random_n_tasks(self, n: int = 20, weighted: bool = True) -> List[Task]:
        """
        Get N random incomplete tasks, optionally weighted by priority

        Args:
            n: Number of tasks to return
            weighted: If True, higher priority tasks are more likely

        Returns:
            List of N random tasks
        """
        import random

        incomplete = self.get_incomplete_tasks()
        if len(incomplete) <= n:
            return incomplete

        if not weighted:
            return random.sample(incomplete, n)

        # Weight by priority: P0=4, P1=3, P2=2, P3=1
        weights = [4 - task.priority.value for task in incomplete]
        return random.choices(incomplete, weights=weights, k=n)

    def get_statistics(self) -> Dict[str, int]:
        """Get task statistics"""
        total = len(self.tasks)
        completed = len(self.get_completed_tasks())
        incomplete = len(self.get_incomplete_tasks())

        by_priority = {
            f"P{p.value}": len(self.get_tasks_by_priority(p))
            for p in Priority
        }

        return {
            "total": total,
            "completed": completed,
            "incomplete": incomplete,
            "completion_rate": round(completed / total * 100, 1) if total > 0 else 0,
            **by_priority
        }

    def search_tasks(self, query: str, case_sensitive: bool = False) -> List[Task]:
        """
        Search tasks by keyword in title or description

        Args:
            query: Search query
            case_sensitive: Whether to match case

        Returns:
            List of matching tasks
        """
        if not case_sensitive:
            query = query.lower()

        matches = []
        for task in self.tasks:
            text = task.title + " " + task.description
            if not case_sensitive:
                text = text.lower()

            if query in text:
                matches.append(task)

        return matches

    def filter_tasks(
        self,
        priority: Optional[Priority] = None,
        effort: Optional[Effort] = None,
        section: Optional[str] = None,
        completed: Optional[bool] = None
    ) -> List[Task]:
        """
        Filter tasks by various criteria

        Args:
            priority: Filter by priority level
            effort: Filter by effort estimate
            section: Filter by section name
            completed: Filter by completion status

        Returns:
            List of filtered tasks
        """
        filtered = self.tasks

        if priority is not None:
            filtered = [t for t in filtered if t.priority == priority]

        if effort is not None:
            filtered = [t for t in filtered if t.effort == effort]

        if section is not None:
            filtered = [t for t in filtered if section.lower() in t.section.lower()]

        if completed is not None:
            filtered = [t for t in filtered if t.completed == completed]

        return filtered


def main():
    """Example usage"""
    parser = TodoParser()
    tasks = parser.parse()

    print(f"Parsed {len(tasks)} tasks")
    print(f"\nStatistics: {parser.get_statistics()}")

    print(f"\nTop 5 tasks:")
    for task in parser.get_top_n_tasks(5):
        print(f"  {task}")

    print(f"\nP0 incomplete tasks: {len(parser.filter_tasks(priority=Priority.P0, completed=False))}")


if __name__ == "__main__":
    main()
