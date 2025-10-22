"""
Git Rollback Mechanism for AI Agent Changes

Provides safe rollback functionality for AI agent commits with
one-click revert and state restoration.
"""

import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from datetime import datetime
import json


class RollbackManager:
    """Manages git rollback operations for AI agent commits"""

    def __init__(self, repo_path: str = "."):
        """
        Initialize rollback manager

        Args:
            repo_path: Path to git repository root
        """
        self.repo_path = Path(repo_path)
        self.snapshots_file = self.repo_path / ".improve_snapshots.json"
        self._ensure_git_repo()

    def _ensure_git_repo(self):
        """Verify we're in a git repository"""
        try:
            subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError:
            raise RuntimeError(f"Not a git repository: {self.repo_path}")

    def create_snapshot(self, description: str = "") -> str:
        """
        Create a snapshot of current state before agent actions

        Args:
            description: Description of what's about to happen

        Returns:
            Snapshot ID (git commit hash)
        """
        # Get current commit hash
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        commit_hash = result.stdout.strip()

        # Save snapshot metadata
        snapshot = {
            "id": commit_hash,
            "timestamp": datetime.now().isoformat(),
            "description": description,
            "branch": self._get_current_branch()
        }

        self._save_snapshot(snapshot)
        return commit_hash

    def rollback_to_commit(self, commit_hash: str, hard: bool = False) -> bool:
        """
        Rollback to a specific commit

        Args:
            commit_hash: Git commit hash to rollback to
            hard: If True, use hard reset (discards changes). If False, use soft reset

        Returns:
            True if successful
        """
        try:
            # Verify commit exists
            subprocess.run(
                ["git", "cat-file", "-e", commit_hash],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )

            # Perform reset
            reset_type = "--hard" if hard else "--soft"
            subprocess.run(
                ["git", "reset", reset_type, commit_hash],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )

            return True
        except subprocess.CalledProcessError:
            return False

    def revert_last_n_commits(self, n: int = 1) -> bool:
        """
        Revert the last N commits (creates new revert commits)

        Args:
            n: Number of commits to revert

        Returns:
            True if successful
        """
        try:
            # Get the last N commit hashes
            result = subprocess.run(
                ["git", "log", f"-{n}", "--format=%H"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            commits = result.stdout.strip().split('\n')

            # Revert each commit (in reverse order for proper revert)
            for commit in reversed(commits):
                subprocess.run(
                    ["git", "revert", "--no-edit", commit],
                    cwd=self.repo_path,
                    check=True,
                    capture_output=True
                )

            return True
        except subprocess.CalledProcessError:
            return False

    def get_agent_commits(self, agent_id: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """
        Get commits made by AI agents

        Args:
            agent_id: Filter by specific agent ID (None for all agents)
            limit: Maximum number of commits to return

        Returns:
            List of commit dictionaries
        """
        try:
            # Get commits with "Co-Authored-By: Claude" in message
            result = subprocess.run(
                [
                    "git", "log",
                    f"-{limit}",
                    "--grep=Co-Authored-By: Claude",
                    "--format=%H|%an|%ae|%at|%s"
                ],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )

            commits = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                parts = line.split('|', 4)
                if len(parts) == 5:
                    commits.append({
                        "hash": parts[0],
                        "author": parts[1],
                        "email": parts[2],
                        "timestamp": int(parts[3]),
                        "message": parts[4]
                    })

            return commits
        except subprocess.CalledProcessError:
            return []

    def get_diff_for_commit(self, commit_hash: str) -> str:
        """
        Get the diff for a specific commit

        Args:
            commit_hash: Git commit hash

        Returns:
            Diff output as string
        """
        try:
            result = subprocess.run(
                ["git", "show", "--format=", commit_hash],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError:
            return ""

    def get_changed_files(self, commit_hash: str) -> List[str]:
        """
        Get list of files changed in a commit

        Args:
            commit_hash: Git commit hash

        Returns:
            List of file paths
        """
        try:
            result = subprocess.run(
                ["git", "show", "--name-only", "--format=", commit_hash],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
            return files
        except subprocess.CalledProcessError:
            return []

    def cherry_pick_commit(self, commit_hash: str) -> bool:
        """
        Cherry-pick a specific commit

        Args:
            commit_hash: Git commit hash to cherry-pick

        Returns:
            True if successful
        """
        try:
            subprocess.run(
                ["git", "cherry-pick", commit_hash],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def _get_current_branch(self) -> str:
        """Get current git branch name"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "unknown"

    def _save_snapshot(self, snapshot: Dict):
        """Save snapshot metadata to file"""
        snapshots = []
        if self.snapshots_file.exists():
            with open(self.snapshots_file, 'r') as f:
                snapshots = json.load(f)

        snapshots.append(snapshot)

        # Keep only last 100 snapshots
        snapshots = snapshots[-100:]

        with open(self.snapshots_file, 'w') as f:
            json.dump(snapshots, f, indent=2)

    def get_snapshots(self, limit: int = 10) -> List[Dict]:
        """
        Get recent snapshots

        Args:
            limit: Maximum number of snapshots to return

        Returns:
            List of snapshot dictionaries
        """
        if not self.snapshots_file.exists():
            return []

        with open(self.snapshots_file, 'r') as f:
            snapshots = json.load(f)

        return snapshots[-limit:]

    def can_rollback(self) -> Tuple[bool, str]:
        """
        Check if rollback is safe (no uncommitted changes)

        Returns:
            Tuple of (can_rollback, reason)
        """
        try:
            # Check for uncommitted changes
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )

            if result.stdout.strip():
                return False, "Uncommitted changes present"

            return True, "Safe to rollback"
        except subprocess.CalledProcessError:
            return False, "Git error"


def main():
    """Example usage"""
    manager = RollbackManager()

    # Create snapshot before changes
    snapshot_id = manager.create_snapshot("Before AI agent batch processing")
    print(f"Created snapshot: {snapshot_id}")

    # Get recent agent commits
    commits = manager.get_agent_commits(limit=5)
    print(f"\nRecent agent commits: {len(commits)}")
    for commit in commits:
        print(f"  {commit['hash'][:7]} - {commit['message']}")

    # Check if can rollback
    can_rollback, reason = manager.can_rollback()
    print(f"\nCan rollback: {can_rollback} ({reason})")


if __name__ == "__main__":
    main()
