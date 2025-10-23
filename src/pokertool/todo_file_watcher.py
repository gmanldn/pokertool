"""TODO.md File Watcher - Watch for external changes and notify"""
import os
import time
import hashlib
import logging
from typing import Optional, Callable, Dict
from pathlib import Path
from threading import Thread, Event
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class FileChange:
    """Represents a file change event"""
    timestamp: datetime
    file_path: str
    old_hash: str
    new_hash: str
    size: int


class TodoFileWatcher:
    """Watch TODO.md for external changes"""

    def __init__(self, file_path: str = "docs/TODO.md", poll_interval: float = 2.0):
        """
        Initialize file watcher

        Args:
            file_path: Path to TODO.md file
            poll_interval: How often to check for changes (seconds)
        """
        self.file_path = Path(file_path)
        self.poll_interval = poll_interval
        self.is_watching = False
        self.stop_event = Event()
        self.watch_thread: Optional[Thread] = None

        # State tracking
        self.last_hash: Optional[str] = None
        self.last_modified: Optional[float] = None
        self.last_size: Optional[int] = None

        # Callbacks
        self.on_change: Optional[Callable[[FileChange], None]] = None
        self.on_conflict: Optional[Callable[[FileChange], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None

        # Conflict detection
        self.pending_writes: Dict[str, float] = {}  # hash -> timestamp
        self.conflict_window = 1.0  # seconds

    def _compute_hash(self, content: bytes) -> str:
        """Compute SHA256 hash of file content"""
        return hashlib.sha256(content).hexdigest()

    def _read_file_state(self) -> Optional[tuple[str, int, float]]:
        """Read current file state (hash, size, mtime)"""
        try:
            if not self.file_path.exists():
                return None

            stat = os.stat(self.file_path)
            with open(self.file_path, 'rb') as f:
                content = f.read()

            file_hash = self._compute_hash(content)
            return file_hash, stat.st_size, stat.st_mtime

        except Exception as e:
            logger.error(f"Error reading file state: {e}")
            return None

    def start(self):
        """Start watching the file"""
        if self.is_watching:
            logger.warning("File watcher already running")
            return

        # Initialize state
        state = self._read_file_state()
        if state:
            self.last_hash, self.last_size, self.last_modified = state

        self.is_watching = True
        self.stop_event.clear()
        self.watch_thread = Thread(target=self._watch_loop, daemon=True)
        self.watch_thread.start()

        logger.info(f"Started watching {self.file_path}")

    def stop(self):
        """Stop watching the file"""
        if not self.is_watching:
            return

        self.is_watching = False
        self.stop_event.set()

        if self.watch_thread:
            self.watch_thread.join(timeout=5.0)
            self.watch_thread = None

        logger.info(f"Stopped watching {self.file_path}")

    def _watch_loop(self):
        """Main watch loop (runs in background thread)"""
        while not self.stop_event.is_set():
            try:
                self._check_for_changes()
            except Exception as e:
                logger.error(f"Error in watch loop: {e}")
                if self.on_error:
                    self.on_error(e)

            # Wait for next poll
            self.stop_event.wait(self.poll_interval)

    def _check_for_changes(self):
        """Check if file has changed"""
        state = self._read_file_state()
        if not state:
            return

        new_hash, new_size, new_mtime = state

        # Check if file changed
        if self.last_hash is not None and new_hash != self.last_hash:
            # File changed externally
            change = FileChange(
                timestamp=datetime.now(),
                file_path=str(self.file_path),
                old_hash=self.last_hash,
                new_hash=new_hash,
                size=new_size
            )

            # Check for conflict (change happened during our write)
            is_conflict = self._is_conflict(new_hash, new_mtime)

            if is_conflict:
                logger.warning(f"Conflict detected in {self.file_path}")
                if self.on_conflict:
                    self.on_conflict(change)
            else:
                logger.info(f"External change detected in {self.file_path}")
                if self.on_change:
                    self.on_change(change)

        # Update state
        self.last_hash = new_hash
        self.last_size = new_size
        self.last_modified = new_mtime

    def _is_conflict(self, new_hash: str, new_mtime: float) -> bool:
        """Check if change is a conflict with our pending write"""
        # Clean up old pending writes
        current_time = time.time()
        self.pending_writes = {
            h: t for h, t in self.pending_writes.items()
            if current_time - t < self.conflict_window * 2
        }

        # Check if any pending write is in conflict window
        for pending_hash, pending_time in self.pending_writes.items():
            time_diff = abs(new_mtime - pending_time)
            if time_diff < self.conflict_window and new_hash != pending_hash:
                return True

        return False

    def register_write(self, expected_hash: str):
        """
        Register that we're about to write to the file

        Args:
            expected_hash: Expected hash after our write
        """
        self.pending_writes[expected_hash] = time.time()

    def get_current_hash(self) -> Optional[str]:
        """Get current file hash"""
        return self.last_hash

    def is_modified_since(self, timestamp: float) -> bool:
        """Check if file was modified since timestamp"""
        if self.last_modified is None:
            return False
        return self.last_modified > timestamp

    def get_stats(self) -> Dict:
        """Get watcher statistics"""
        return {
            "watching": self.is_watching,
            "file_path": str(self.file_path),
            "last_hash": self.last_hash,
            "last_size": self.last_size,
            "last_modified": datetime.fromtimestamp(self.last_modified) if self.last_modified else None,
            "pending_writes": len(self.pending_writes)
        }


class TodoSyncManager:
    """Manage TODO.md synchronization with conflict detection"""

    def __init__(self, file_path: str = "docs/TODO.md"):
        self.watcher = TodoFileWatcher(file_path)
        self.conflict_detected = False
        self.latest_change: Optional[FileChange] = None

        # Set up callbacks
        self.watcher.on_change = self._handle_change
        self.watcher.on_conflict = self._handle_conflict

    def start(self):
        """Start sync manager"""
        self.watcher.start()

    def stop(self):
        """Stop sync manager"""
        self.watcher.stop()

    def _handle_change(self, change: FileChange):
        """Handle external file change"""
        self.latest_change = change
        logger.info(f"TODO.md changed externally at {change.timestamp}")

    def _handle_conflict(self, change: FileChange):
        """Handle write conflict"""
        self.conflict_detected = True
        self.latest_change = change
        logger.warning(f"TODO.md conflict detected at {change.timestamp}")

    def has_conflict(self) -> bool:
        """Check if conflict detected"""
        return self.conflict_detected

    def clear_conflict(self):
        """Clear conflict flag"""
        self.conflict_detected = False

    def get_latest_change(self) -> Optional[FileChange]:
        """Get latest change event"""
        return self.latest_change

    def safe_write(self, write_func: Callable[[], str]) -> bool:
        """
        Safely write to TODO.md with conflict detection

        Args:
            write_func: Function that performs write and returns new hash

        Returns:
            True if write succeeded without conflict
        """
        # Get current state
        current_hash = self.watcher.get_current_hash()

        # Perform write
        try:
            new_hash = write_func()
            self.watcher.register_write(new_hash)

            # Wait briefly to detect conflicts
            time.sleep(0.5)

            # Check for conflict
            if self.has_conflict():
                logger.error("Write conflict detected")
                return False

            return True

        except Exception as e:
            logger.error(f"Error during safe write: {e}")
            return False
