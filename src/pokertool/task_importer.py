"""Task Importer - Import tasks from various formats into TODO.md"""
import csv
import json
import re
import logging
from typing import List, Dict, Optional
from pathlib import Path
from dataclasses import dataclass

from pokertool.todo_updater import TodoUpdater
from pokertool.todo_parser import Priority, Effort

logger = logging.getLogger(__name__)


@dataclass
class ImportedTask:
    """Represents a task to be imported"""
    title: str
    description: Optional[str] = None
    priority: Priority = Priority.P1
    effort: Effort = Effort.M
    file_path: Optional[str] = None


class TaskImporter:
    """Import tasks from various formats"""

    def __init__(self, todo_path: str = "docs/TODO.md"):
        self.todo_path = todo_path
        self.updater = TodoUpdater(todo_path)

    def import_from_text(self, text: str) -> List[ImportedTask]:
        """
        Import tasks from plain text (one per line or numbered list)

        Formats supported:
        - "Task title"
        - "1. Task title"
        - "- Task title"
        - "[P0][M] Task title — Description"
        """
        tasks = []
        lines = text.strip().split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Try to parse existing TODO.md format
            task = self._parse_todo_line(line)
            if task:
                tasks.append(task)
                continue

            # Remove list markers
            line = re.sub(r'^(\d+\.|\-|\*)\s+', '', line)

            # Create basic task
            if line:
                tasks.append(ImportedTask(title=line))

        return tasks

    def import_from_csv(self, csv_path: str) -> List[ImportedTask]:
        """
        Import tasks from CSV file

        Expected columns: title, description, priority, effort, file_path
        (Only title is required)
        """
        tasks = []

        try:
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    if not row.get('title'):
                        continue

                    task = ImportedTask(
                        title=row['title'].strip(),
                        description=row.get('description', '').strip() or None,
                        priority=self._parse_priority(row.get('priority', 'P1')),
                        effort=self._parse_effort(row.get('effort', 'M')),
                        file_path=row.get('file_path', '').strip() or None
                    )
                    tasks.append(task)

            logger.info(f"Imported {len(tasks)} tasks from CSV: {csv_path}")
            return tasks

        except Exception as e:
            logger.error(f"Failed to import CSV: {e}")
            return []

    def import_from_json(self, json_path: str) -> List[ImportedTask]:
        """
        Import tasks from JSON file

        Expected format:
        [
          {
            "title": "Task title",
            "description": "Optional description",
            "priority": "P0",
            "effort": "M",
            "file_path": "optional/path.py"
          }
        ]
        """
        tasks = []

        try:
            with open(json_path, 'r') as f:
                data = json.load(f)

            if not isinstance(data, list):
                logger.error("JSON must contain an array of tasks")
                return []

            for item in data:
                if not item.get('title'):
                    continue

                task = ImportedTask(
                    title=item['title'].strip(),
                    description=item.get('description', '').strip() or None,
                    priority=self._parse_priority(item.get('priority', 'P1')),
                    effort=self._parse_effort(item.get('effort', 'M')),
                    file_path=item.get('file_path', '').strip() or None
                )
                tasks.append(task)

            logger.info(f"Imported {len(tasks)} tasks from JSON: {json_path}")
            return tasks

        except Exception as e:
            logger.error(f"Failed to import JSON: {e}")
            return []

    def import_from_todo_file(self, todo_path: str) -> List[ImportedTask]:
        """Import tasks from another TODO.md file"""
        tasks = []

        try:
            with open(todo_path, 'r') as f:
                lines = f.readlines()

            for line in lines:
                task = self._parse_todo_line(line.strip())
                if task:
                    tasks.append(task)

            logger.info(f"Imported {len(tasks)} tasks from TODO file: {todo_path}")
            return tasks

        except Exception as e:
            logger.error(f"Failed to import TODO file: {e}")
            return []

    def add_tasks_to_todo(self, tasks: List[ImportedTask], section: Optional[str] = None) -> int:
        """
        Add imported tasks to TODO.md

        Args:
            tasks: List of tasks to add
            section: Optional section header to add tasks under

        Returns:
            Number of tasks successfully added
        """
        count = 0

        for task in tasks:
            try:
                success = self.updater.add_task(
                    title=task.title,
                    description=task.description or "",
                    priority=task.priority,
                    effort=task.effort,
                    file_path=task.file_path
                )
                if success:
                    count += 1
            except Exception as e:
                logger.error(f"Failed to add task '{task.title}': {e}")

        logger.info(f"Added {count}/{len(tasks)} tasks to TODO.md")
        return count

    def _parse_todo_line(self, line: str) -> Optional[ImportedTask]:
        """Parse a line in TODO.md format"""
        # Match: - [ ] [P0][M] Title — Description `file.py`
        pattern = r'^\-\s+\[\s?\]\s+\[([P0-3])\]\[([SML])\]\s+(.+?)(?:\s+—\s+(.+?))?(?:\s+`([^`]+)`)?$'
        match = re.match(pattern, line)

        if match:
            priority_str, effort_str, title, description, file_path = match.groups()

            return ImportedTask(
                title=title.strip(),
                description=description.strip() if description else None,
                priority=self._parse_priority(priority_str),
                effort=self._parse_effort(effort_str),
                file_path=file_path.strip() if file_path else None
            )

        return None

    def _parse_priority(self, priority_str: str) -> Priority:
        """Parse priority string to Priority enum"""
        priority_str = priority_str.upper().strip()
        if priority_str in ['P0', '0']:
            return Priority.P0
        elif priority_str in ['P1', '1']:
            return Priority.P1
        elif priority_str in ['P2', '2']:
            return Priority.P2
        elif priority_str in ['P3', '3']:
            return Priority.P3
        else:
            return Priority.P1  # Default

    def _parse_effort(self, effort_str: str) -> Effort:
        """Parse effort string to Effort enum"""
        effort_str = effort_str.upper().strip()
        if effort_str in ['S', 'SMALL']:
            return Effort.S
        elif effort_str in ['M', 'MEDIUM']:
            return Effort.M
        elif effort_str in ['L', 'LARGE']:
            return Effort.L
        else:
            return Effort.M  # Default

    def preview_import(self, tasks: List[ImportedTask]) -> str:
        """Generate preview of tasks to be imported"""
        lines = ["Import Preview", "=" * 60, ""]

        for i, task in enumerate(tasks, 1):
            desc = f" — {task.description}" if task.description else ""
            file = f" `{task.file_path}`" if task.file_path else ""
            line = f"{i}. [{task.priority.value}][{task.effort.value}] {task.title}{desc}{file}"
            lines.append(line)

        lines.append("")
        lines.append("=" * 60)
        lines.append(f"Total: {len(tasks)} tasks")

        return "\n".join(lines)
