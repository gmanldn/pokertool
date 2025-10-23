"""Anthropic API Provider - Direct API integration with Claude 3.5 Sonnet"""
import asyncio
import json
import logging
import os
from typing import Optional, Dict, Any, List, AsyncIterator
import aiohttp

from pokertool.ai_providers.base_provider import BaseAIProvider

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseAIProvider):
    """Direct Anthropic API integration"""

    API_URL = "https://api.anthropic.com/v1/messages"
    DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
    MAX_TOKENS = 8192

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model or self.DEFAULT_MODEL
        self.session: Optional[aiohttp.ClientSession] = None

    def validate_api_key(self) -> bool:
        """Validate API key is set"""
        return bool(self.api_key)

    async def initialize(self) -> bool:
        """Initialize HTTP session"""
        if not self.api_key:
            logger.error("Anthropic API key not set")
            return False

        self.session = aiohttp.ClientSession(
            headers={
                "anthropic-version": "2023-06-01",
                "x-api-key": self.api_key,
                "content-type": "application/json"
            }
        )
        return True

    async def generate_response(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> str:
        """
        Send prompt to Anthropic API and get response

        Args:
            prompt: The user prompt
            context: Additional context (system prompt, previous messages)
            stream: Whether to stream the response

        Returns:
            Response from Claude
        """
        if not self.session:
            await self.initialize()

        try:
            # Build messages
            messages = [{"role": "user", "content": prompt}]

            # Add context messages if provided
            if context and "messages" in context:
                messages = context["messages"] + messages

            # Build request payload
            payload = {
                "model": self.model,
                "max_tokens": self.MAX_TOKENS,
                "messages": messages
            }

            # Add system prompt if provided
            if context and "system" in context:
                payload["system"] = context["system"]

            # Make API request
            if stream:
                return await self._stream_response(payload)
            else:
                return await self._get_response(payload)

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    async def _get_response(self, payload: Dict[str, Any]) -> str:
        """Get non-streaming response"""
        async with self.session.post(self.API_URL, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"API error: {error_text}")
                raise Exception(f"Anthropic API error: {error_text}")

            data = await response.json()
            return data["content"][0]["text"]

    async def _stream_response(self, payload: Dict[str, Any]) -> str:
        """Get streaming response"""
        payload["stream"] = True
        full_response = []

        async with self.session.post(self.API_URL, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"API error: {error_text}")
                raise Exception(f"Anthropic API error: {error_text}")

            async for line in response.content:
                if line:
                    line_text = line.decode('utf-8').strip()
                    if line_text.startswith('data: '):
                        json_str = line_text[6:]
                        if json_str == '[DONE]':
                            break
                        try:
                            event = json.loads(json_str)
                            if event.get("type") == "content_block_delta":
                                delta = event.get("delta", {})
                                if "text" in delta:
                                    full_response.append(delta["text"])
                        except json.JSONDecodeError:
                            pass

        return "".join(full_response)

    async def execute_task(
        self,
        task_description: str,
        file_paths: Optional[List[str]] = None,
        working_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a task using Claude API

        Args:
            task_description: Description of the task
            file_paths: Relevant file paths to provide as context
            working_dir: Working directory for execution

        Returns:
            Dict with status, output, files_changed, etc.
        """
        try:
            # Build context with file contents
            context = {
                "system": """You are an expert software engineer.
You will be given a task to complete. Analyze the task, create a plan,
and provide the implementation details including:
1. Files to modify
2. Code changes needed
3. Tests to add
4. Commit message

Respond in JSON format."""
            }

            # Read file contents if provided
            if file_paths:
                files_content = []
                for file_path in file_paths:
                    try:
                        with open(file_path, 'r') as f:
                            files_content.append(f"File: {file_path}\n{f.read()}")
                    except Exception as e:
                        logger.warning(f"Could not read {file_path}: {e}")

                if files_content:
                    task_description += "\n\nContext files:\n" + "\n\n".join(files_content)

            # Generate response
            response = await self.generate_response(task_description, context)

            # Try to parse JSON response
            try:
                result = json.loads(response)
                result["status"] = "success"
                return result
            except json.JSONDecodeError:
                # Return raw response if not JSON
                return {
                    "status": "success",
                    "output": response,
                    "files_changed": [],
                    "tests_passed": None,
                    "commit_message": None
                }

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
        context = {
            "system": "You are an expert software engineer creating implementation plans."
        }

        prompt = f"""Create a detailed step-by-step plan for the following task:

{task_description}

Provide:
1. A numbered list of implementation steps
2. Files that need to be created or modified
3. Key technical considerations
4. Testing strategy"""

        return await self.generate_response(prompt, context)

    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
            self.session = None
