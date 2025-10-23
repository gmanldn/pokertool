"""
TODO.md Updater Module

Updates TODO.md file to mark tasks as complete, add progress notes,
and maintain task completion history.
"""

import re
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from .todo_parser import TodoParser, Task, Priority, Effort


class TodoUpdater:
    """Updates TODO.md file with task completion status"""

    def __init__(self, todo_file: str = "docs/TODO.md"):
        """
        Initialize updater with path to TODO.md

        Args:
            todo_file: Path to TODO.md file relative to project root
        """
        self.todo_file = Path(todo_file)
        self.parser = TodoParser(str(todo_file))

    def mark_task_complete(
        self,
        task: Task,
        completion_note: Optional[str] = None,
        commit_hash: Optional[str] = None
    ) -> bool:
        """
        Mark a task as complete in TODO.md

        Args:
            task: Task object to mark complete
            completion_note: Optional note about how task was completed
            commit_hash: Optional git commit hash

        Returns:
            True if successful, False otherwise
        """
        if not self.todo_file.exists():
            return False

        # Read file
        with open(self.todo_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Find and update the task line
        if task.line_number > len(lines):
            return False

        # Get the original line (1-indexed to 0-indexed)
        line_idx = task.line_number - 1
        original_line = lines[line_idx].rstrip()

        # Create updated line
        updated_line = self._create_completed_line(
            original_line, task, completion_note, commit_hash
        )

        # Update the line
        lines[line_idx] = updated_line + '\n'

        # Write back to file
        with open(self.todo_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        return True

    def _create_completed_line(
        self,
        original_line: str,
        task: Task,
        completion_note: Optional[str],
        commit_hash: Optional[str]
    ) -> str:
        """Create the completed task line with checkmark and notes"""
        # Replace [ ] with [x]
        updated = original_line.replace('- [ ]', '- [x]', 1)

        # Add completion marker before description
        parts = updated.split(' — ', 1)
        if len(parts) == 2:
            title_part = parts[0]
            desc_part = parts[1]

            # Build completion note
            completion_text = "✅ Complete"
            if completion_note:
                completion_text += f": {completion_note}"
            if commit_hash:
                completion_text += f" (commit: {commit_hash[:7]})"

            updated = f"{title_part} — {completion_text}. {desc_part}"
        else:
            # No description, add at end
            completion_text = "✅ Complete"
            if completion_note:
                completion_text += f": {completion_note}"
            if commit_hash:
                completion_text += f" (commit: {commit_hash[:7]})"

            # Insert before file path if present
            if '`' in updated:
                parts = updated.rsplit('`', 1)
                updated = f"{parts[0].rstrip()} — {completion_text}. `{parts[1]}"
            else:
                updated = f"{updated} — {completion_text}."

        return updated

    def mark_task_in_progress(
        self,
        task: Task,
        agent_id: str
    ) -> bool:
        """
        Add in-progress marker to task (doesn't check box)

        Args:
            task: Task to mark
            agent_id: ID of agent working on task

        Returns:
            True if successful
        """
        if not self.todo_file.exists():
            return False

        with open(self.todo_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if task.line_number > len(lines):
            return False

        line_idx = task.line_number - 1
        original_line = lines[line_idx].rstrip()

        # Add in-progress marker
        if ' — ' in original_line:
            parts = original_line.split(' — ', 1)
            updated = f"{parts[0]} — 🔄 In Progress ({agent_id}). {parts[1]}"
        else:
            if '`' in original_line:
                parts = original_line.rsplit('`', 1)
                updated = f"{parts[0].rstrip()} — 🔄 In Progress ({agent_id}). `{parts[1]}"
            else:
                updated = f"{original_line} — 🔄 In Progress ({agent_id})."

        lines[line_idx] = updated + '\n'

        with open(self.todo_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        return True

    def add_task(
        self,
        title: str,
        description: str,
        priority: Priority,
        effort: Effort,
        file_path: Optional[str] = None,
        section: Optional[str] = None
    ) -> bool:
        """
        Add a new task to TODO.md

        Args:
            title: Task title
            description: Task description
            priority: Task priority
            effort: Task effort estimate
            file_path: Optional file path
            section: Optional section to add to (defaults to end of file)

        Returns:
            True if successful
        """
        # Create task line
        task_line = f"- [ ] [{priority.name}][{effort.name}] {title}"

        if description:
            task_line += f" — {description}"

        if file_path:
            task_line += f". `{file_path}`"

        task_line += "\n"

        if not self.todo_file.exists():
            # Create new file
            with open(self.todo_file, 'w', encoding='utf-8') as f:
                f.write(f"# TODO\n\n## Tasks\n\n{task_line}")
            return True

        # Append to existing file
        with open(self.todo_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find section if specified
        if section:
            section_pattern = re.compile(rf'^##\s+{re.escape(section)}\s*$', re.MULTILINE)
            match = section_pattern.search(content)
            if match:
                # Insert after section header
                insert_pos = match.end()
                # Find next line
                next_newline = content.find('\n', insert_pos)
                if next_newline != -1:
                    insert_pos = next_newline + 1

                content = content[:insert_pos] + task_line + content[insert_pos:]
            else:
                # Section not found, append to end
                content += f"\n{task_line}"
        else:
            # Append to end
            content += f"\n{task_line}"

        with open(self.todo_file, 'w', encoding='utf-8') as f:
            f.write(content)

        return True

    def bulk_mark_complete(
        self,
        tasks: List[Task],
        completion_note: Optional[str] = None
    ) -> int:
        """
        Mark multiple tasks as complete

        Args:
            tasks: List of tasks to mark complete
            completion_note: Optional note for all tasks

        Returns:
            Number of tasks successfully marked complete
        """
        count = 0
        for task in tasks:
            if self.mark_task_complete(task, completion_note):
                count += 1
        return count

    def get_completion_stats(self) -> dict:
        """
        Get updated completion statistics after changes

        Returns:
            Dictionary with completion stats
        """
        # Re-parse to get updated stats
        self.parser = TodoParser(str(self.todo_file))
        self.parser.parse()
        return self.parser.get_statistics()

    def remove_completed_tasks(self, older_than_days: Optional[int] = None) -> int:
        """
        Remove completed tasks from TODO.md (archive them)

        Args:
            older_than_days: Only remove tasks completed more than N days ago

        Returns:
            Number of tasks removed
        """
        # This would require parsing completion dates from the completion notes
        # For now, just return 0 - can be implemented later
        return 0

    def add_section(self, section_name: str, level: int = 2) -> bool:
        """
        Add a new section to TODO.md

        Args:
            section_name: Name of section
            level: Heading level (2 for ##, 3 for ###)

        Returns:
            True if successful
        """
        if not self.todo_file.exists():
            return False

        heading = '#' * level
        section_line = f"\n{heading} {section_name}\n\n"

        with open(self.todo_file, 'a', encoding='utf-8') as f:
            f.write(section_line)

        return True


def main():
    """Example usage"""
    updater = TodoUpdater()

    print("Current stats:", updater.get_completion_stats())

    # Example: Mark a task complete
    # parser = updater.parser
    # parser.parse()
    # if parser.tasks:
    #     task = parser.tasks[0]
    #     updater.mark_task_complete(task, "Implemented parser module", "abc123")
    #     print("\nUpdated stats:", updater.get_completion_stats())


if __name__ == "__main__":
    main()
