"""
Terminal Output Logger for AI Agents

Logs all terminal output from AI agents to rotating log files
with automatic daily rotation and compression.
"""

import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime
from typing import Optional
import gzip
import shutil


class ImproveLogger:
    """Manages logging for AI agent terminal output"""

    def __init__(self, log_dir: str = "logs/improve"):
        """
        Initialize logger

        Args:
            log_dir: Directory for log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.loggers = {}

    def get_agent_logger(self, agent_id: str, max_bytes: int = 10_000_000) -> logging.Logger:
        """
        Get or create logger for specific agent

        Args:
            agent_id: Unique agent identifier
            max_bytes: Maximum log file size before rotation (default 10MB)

        Returns:
            Configured logger instance
        """
        if agent_id in self.loggers:
            return self.loggers[agent_id]

        # Create logger
        logger = logging.getLogger(f"improve.{agent_id}")
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        # Create log file path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"agent_{agent_id}_{timestamp}.log"

        # Rotating file handler (rotates when file reaches max_bytes)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)

        # Format: timestamp | level | message
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        self.loggers[agent_id] = logger

        return logger

    def get_daily_logger(self, agent_id: str) -> logging.Logger:
        """
        Get logger with daily rotation

        Args:
            agent_id: Agent identifier

        Returns:
            Logger with daily rotation
        """
        logger_name = f"improve.daily.{agent_id}"

        if logger_name in self.loggers:
            return self.loggers[logger_name]

        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        # Daily rotating file handler
        log_file = self.log_dir / f"agent_{agent_id}_daily.log"
        file_handler = TimedRotatingFileHandler(
            log_file,
            when='midnight',
            interval=1,
            backupCount=30,  # Keep 30 days
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        self.loggers[logger_name] = logger

        return logger

    def log_terminal_output(self, agent_id: str, output: str, level: str = "INFO"):
        """
        Log terminal output from agent

        Args:
            agent_id: Agent identifier
            output: Terminal output text
            level: Log level (DEBUG, INFO, WARNING, ERROR)
        """
        logger = self.get_agent_logger(agent_id)

        level_map = {
            "DEBUG": logger.debug,
            "INFO": logger.info,
            "WARNING": logger.warning,
            "ERROR": logger.error,
            "CRITICAL": logger.critical
        }

        log_func = level_map.get(level.upper(), logger.info)
        log_func(output)

    def log_agent_action(
        self,
        agent_id: str,
        action: str,
        details: Optional[str] = None
    ):
        """
        Log specific agent action

        Args:
            agent_id: Agent identifier
            action: Action type (e.g., "task_start", "commit", "test_run")
            details: Additional details
        """
        logger = self.get_agent_logger(agent_id)
        message = f"[ACTION:{action}]"
        if details:
            message += f" {details}"
        logger.info(message)

    def log_error(self, agent_id: str, error: str, traceback: Optional[str] = None):
        """
        Log error from agent

        Args:
            agent_id: Agent identifier
            error: Error message
            traceback: Optional traceback string
        """
        logger = self.get_agent_logger(agent_id)
        logger.error(f"ERROR: {error}")
        if traceback:
            logger.error(f"TRACEBACK:\n{traceback}")

    def compress_old_logs(self, days_old: int = 7):
        """
        Compress log files older than specified days

        Args:
            days_old: Compress logs older than this many days
        """
        import time
        cutoff_time = time.time() - (days_old * 24 * 60 * 60)

        for log_file in self.log_dir.glob("*.log"):
            if log_file.stat().st_mtime < cutoff_time:
                # Compress the file
                gz_file = log_file.with_suffix('.log.gz')
                with open(log_file, 'rb') as f_in:
                    with gzip.open(gz_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)

                # Remove original
                log_file.unlink()

    def cleanup_old_logs(self, days_to_keep: int = 30):
        """
        Delete log files older than specified days

        Args:
            days_to_keep: Keep logs for this many days
        """
        import time
        cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)

        for log_file in self.log_dir.glob("*.log*"):
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()

    def get_log_files(self, agent_id: Optional[str] = None) -> list:
        """
        Get list of log files

        Args:
            agent_id: Filter by agent ID (None for all)

        Returns:
            List of log file paths
        """
        if agent_id:
            pattern = f"agent_{agent_id}_*.log*"
        else:
            pattern = "*.log*"

        return sorted(self.log_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)

    def tail_log(self, agent_id: str, lines: int = 100) -> str:
        """
        Get last N lines from agent's log

        Args:
            agent_id: Agent identifier
            lines: Number of lines to return

        Returns:
            Last N lines of log as string
        """
        log_files = self.get_log_files(agent_id)
        if not log_files:
            return ""

        # Get most recent log file
        log_file = log_files[0]

        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return ''.join(all_lines[-lines:])
        except Exception:
            return ""

    def search_logs(self, agent_id: str, query: str, max_results: int = 100) -> list:
        """
        Search through agent logs

        Args:
            agent_id: Agent identifier
            query: Search string
            max_results: Maximum number of results

        Returns:
            List of matching log lines
        """
        results = []
        log_files = self.get_log_files(agent_id)

        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if query.lower() in line.lower():
                            results.append(line.strip())
                            if len(results) >= max_results:
                                return results
            except Exception:
                continue

        return results


# Global logger instance
_global_logger: Optional[ImproveLogger] = None


def get_logger(log_dir: str = "logs/improve") -> ImproveLogger:
    """Get global logger instance"""
    global _global_logger
    if _global_logger is None:
        _global_logger = ImproveLogger(log_dir)
    return _global_logger


def main():
    """Example usage"""
    logger = ImproveLogger()

    # Create agent logger
    agent_logger = logger.get_agent_logger("agent-1")
    agent_logger.info("Agent started")
    agent_logger.debug("Processing task...")
    agent_logger.info("Task completed")

    # Log terminal output
    logger.log_terminal_output("agent-1", "$ git status")
    logger.log_terminal_output("agent-1", "On branch develop")

    # Log action
    logger.log_agent_action("agent-1", "task_start", "Implementing feature X")

    print(f"Logs saved to: {logger.log_dir}")
    print(f"Log files: {len(logger.get_log_files())}")


if __name__ == "__main__":
    main()
