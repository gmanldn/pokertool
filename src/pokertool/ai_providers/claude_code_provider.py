"""Claude Code CLI Provider - Integration with Claude Code CLI"""
import asyncio
import json
import logging
import subprocess
import os
from typing import Optional, Dict, Any, List

from pokertool.ai_providers.base_provider import BaseAIProvider

logger = logging.getLogger(__name__)


class ClaudeCodeProvider(BaseAIProvider):
    """Claude Code CLI integration"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.process: Optional[asyncio.subprocess.Process] = None
        self.session_active = False

    def validate_api_key(self) -> bool:
        """Validate API key is set"""
        return bool(self.api_key)

    async def initialize(self) -> bool:
        """Initialize Claude Code CLI session"""
        try:
            # Check if claude-code is available
            result = await asyncio.create_subprocess_exec(
                "claude-code", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                logger.error("Claude Code CLI not found. Please install it first.")
                return False

            logger.info(f"Claude Code version: {stdout.decode().strip()}")
            self.session_active = True
            return True

        except FileNotFoundError:
            logger.error("Claude Code CLI not found in PATH")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize Claude Code: {e}")
            return False

    async def generate_response(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> str:
        """
        Send prompt to Claude Code CLI and get response

        Args:
            prompt: The task description/prompt
            context: Additional context (files, task info, etc.)
            stream: Whether to stream responses

        Returns:
            Response from Claude Code
        """
        try:
            # Build command
            cmd = ["claude-code"]

            # Add context files if provided
            if context and "files" in context:
                for file_path in context["files"]:
                    cmd.extend(["--file", file_path])

            # Add prompt
            cmd.append(prompt)

            # Execute command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "ANTHROPIC_API_KEY": self.api_key} if self.api_key else None
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                logger.error(f"Claude Code failed: {error_msg}")
                raise Exception(f"Claude Code error: {error_msg}")

            response = stdout.decode().strip()
            return response

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    async def execute_task(
        self,
        task_description: str,
        file_paths: Optional[List[str]] = None,
        working_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a complete task using Claude Code

        Args:
            task_description: Description of the task
            file_paths: Relevant file paths to provide as context
            working_dir: Working directory for execution

        Returns:
            Dict with status, output, files_changed, etc.
        """
        try:
            # Build context
            context = {}
            if file_paths:
                context["files"] = file_paths

            # Generate response
            response = await self.generate_response(task_description, context)

            # Parse response
            # TODO: Parse Claude Code's output format
            result = {
                "status": "success",
                "output": response,
                "files_changed": [],
                "tests_passed": True,
                "commit_message": None
            }

            return result

        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "output": "",
                "files_changed": []
            }

    async def plan_task(self, task_description: str) -> str:
        """
        Generate a plan for executing a task

        Args:
            task_description: Description of the task

        Returns:
            Step-by-step plan
        """
        prompt = f"""Please create a detailed step-by-step plan for the following task:

{task_description}

Provide a numbered list of steps to complete this task."""

        return await self.generate_response(prompt)

    async def cleanup(self):
        """Cleanup resources"""
        if self.process and self.process.returncode is None:
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()

        self.session_active = False
