"""OpenRouter Provider - Multi-model support via OpenRouter API"""
import asyncio
import json
import logging
import os
from typing import Optional, Dict, Any, List
import aiohttp

from pokertool.ai_providers.base_provider import BaseAIProvider

logger = logging.getLogger(__name__)


class OpenRouterProvider(BaseAIProvider):
    """OpenRouter API integration supporting multiple models"""

    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    DEFAULT_MODEL = "anthropic/claude-3.5-sonnet"  # Can also use gpt-4, etc.

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = model or self.DEFAULT_MODEL
        self.session: Optional[aiohttp.ClientSession] = None

    def validate_api_key(self) -> bool:
        """Validate API key is set"""
        return bool(self.api_key)

    async def initialize(self) -> bool:
        """Initialize HTTP session"""
        if not self.api_key:
            logger.error("OpenRouter API key not set")
            return False

        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/pokertool",  # Required by OpenRouter
                "X-Title": "PokerTool AI Agent"
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
        Send prompt to OpenRouter API and get response

        Args:
            prompt: The user prompt
            context: Additional context (system prompt, previous messages)
            stream: Whether to stream the response

        Returns:
            Response from the model
        """
        if not self.session:
            await self.initialize()

        try:
            # Build messages
            messages = []

            # Add system message if provided
            if context and "system" in context:
                messages.append({"role": "system", "content": context["system"]})

            # Add context messages if provided
            if context and "messages" in context:
                messages.extend(context["messages"])

            # Add user message
            messages.append({"role": "user", "content": prompt})

            # Build request payload
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 8192,
                "temperature": 0.7
            }

            if stream:
                payload["stream"] = True

            # Make API request
            async with self.session.post(self.API_URL, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"OpenRouter API error: {error_text}")
                    raise Exception(f"OpenRouter error: {error_text}")

                if stream:
                    return await self._handle_stream(response)
                else:
                    data = await response.json()
                    return data["choices"][0]["message"]["content"]

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    async def _handle_stream(self, response: aiohttp.ClientResponse) -> str:
        """Handle streaming response"""
        full_response = []

        async for line in response.content:
            if line:
                line_text = line.decode('utf-8').strip()
                if line_text.startswith('data: '):
                    json_str = line_text[6:]
                    if json_str == '[DONE]':
                        break
                    try:
                        event = json.loads(json_str)
                        if "choices" in event:
                            delta = event["choices"][0].get("delta", {})
                            if "content" in delta:
                                full_response.append(delta["content"])
                    except json.JSONDecodeError:
                        pass

        return "".join(full_response)

    async def execute_task(
        self,
        task_description: str,
        file_paths: Optional[List[str]] = None,
        working_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a task using OpenRouter"""
        try:
            context = {
                "system": """You are an expert software engineer.
Analyze the task and provide implementation details in JSON format:
{
  "plan": "step-by-step plan",
  "files": ["list of files to modify"],
  "changes": "description of changes",
  "tests": "testing strategy",
  "commit_message": "suggested commit message"
}"""
            }

            # Add file contents if provided
            if file_paths:
                files_content = []
                for file_path in file_paths:
                    try:
                        with open(file_path, 'r') as f:
                            files_content.append(f"File: {file_path}\n{f.read()}")
                    except Exception as e:
                        logger.warning(f"Could not read {file_path}: {e}")

                if files_content:
                    task_description += "\n\nContext:\n" + "\n\n".join(files_content)

            response = await self.generate_response(task_description, context)

            # Try to parse JSON
            try:
                result = json.loads(response)
                result["status"] = "success"
                return result
            except json.JSONDecodeError:
                return {
                    "status": "success",
                    "output": response,
                    "files_changed": []
                }

        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "output": ""
            }

    async def plan_task(self, task_description: str) -> str:
        """Generate execution plan"""
        context = {
            "system": "You are an expert software engineer creating implementation plans."
        }

        prompt = f"""Create a detailed plan for: {task_description}

Include:
1. Implementation steps
2. Files to modify
3. Technical considerations
4. Testing approach"""

        return await self.generate_response(prompt, context)

    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
            self.session = None
