# Claude Code CLI Integration Guide

## Overview

This document outlines best practices for integrating Claude Code CLI as a subprocess for automated AI development tasks in the PokerTool Improve tab.

## Architecture

### Subprocess Management

```python
import asyncio
import subprocess
from typing import Optional, Dict, Any

class ClaudeCodeAgent:
    """Manages Claude Code CLI subprocess for automated tasks"""

    def __init__(self, agent_id: str, workspace_dir: str):
        self.agent_id = agent_id
        self.workspace_dir = workspace_dir
        self.process: Optional[asyncio.subprocess.Process] = None
        self.output_buffer = []

    async def start(self, task: str) -> None:
        """
        Start Claude Code subprocess with task

        Args:
            task: The task description to send to Claude Code
        """
        # Spawn Claude Code as subprocess
        self.process = await asyncio.create_subprocess_exec(
            'claude-code',
            '--no-interactive',  # Disable interactive prompts
            '--json-output',     # Request JSON-formatted responses
            '--task', task,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.workspace_dir
        )
```

### Communication Protocols

#### 1. **Standard Input/Output**
```python
async def send_input(self, input_text: str) -> None:
    """Send input to Claude Code stdin"""
    if self.process and self.process.stdin:
        self.process.stdin.write(f"{input_text}\n".encode())
        await self.process.stdin.drain()

async def read_output(self) -> str:
    """Read output from Claude Code stdout"""
    if self.process and self.process.stdout:
        line = await self.process.stdout.readline()
        return line.decode().strip()
    return ""
```

#### 2. **JSON Mode** (Recommended)
```python
async def parse_json_response(self) -> Dict[str, Any]:
    """
    Parse JSON response from Claude Code

    Expected format:
    {
        "type": "status" | "output" | "action" | "complete" | "error",
        "data": { ... },
        "timestamp": "2025-10-22T10:30:00Z"
    }
    """
    output = await self.read_output()
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {"type": "output", "data": {"text": output}}
```

## Best Practices

### 1. Process Lifecycle Management

```python
async def stop(self, graceful: bool = True) -> None:
    """
    Stop Claude Code subprocess

    Args:
        graceful: If True, send SIGTERM and wait. If False, send SIGKILL.
    """
    if not self.process:
        return

    if graceful:
        # Send graceful shutdown signal
        self.process.terminate()
        try:
            await asyncio.wait_for(self.process.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            # Force kill if graceful shutdown takes too long
            self.process.kill()
            await self.process.wait()
    else:
        # Immediate kill
        self.process.kill()
        await self.process.wait()

    self.process = None
```

### 2. Error Handling

```python
async def monitor_process(self) -> None:
    """Monitor process for errors and unexpected termination"""
    while self.process and self.process.returncode is None:
        try:
            # Read stderr for errors
            if self.process.stderr:
                error_line = await asyncio.wait_for(
                    self.process.stderr.readline(),
                    timeout=0.1
                )
                if error_line:
                    error_text = error_line.decode().strip()
                    await self.handle_error(error_text)
        except asyncio.TimeoutError:
            # No error output, continue monitoring
            pass
        except Exception as e:
            logger.error(f"Error monitoring process: {e}")
            break

        await asyncio.sleep(0.1)

    # Process terminated
    if self.process:
        exit_code = self.process.returncode
        if exit_code != 0:
            await self.handle_unexpected_termination(exit_code)
```

### 3. Interactive Prompt Handling

Claude Code may prompt for user input during execution. Handle this:

```python
async def handle_interactive_prompt(self, prompt_text: str) -> str:
    """
    Handle interactive prompts from Claude Code

    Common prompts:
    - "Proceed with file changes? (y/n)"
    - "Commit these changes? (y/n)"
    - "Run tests before committing? (y/n)"
    """
    # Auto-approve common prompts based on configuration
    auto_approve_patterns = {
        r"Proceed with.*changes": "y",
        r"Commit.*changes": "y",
        r"Run tests": "y",
        r"Approve.*action": "y"
    }

    for pattern, response in auto_approve_patterns.items():
        if re.search(pattern, prompt_text, re.IGNORECASE):
            logger.info(f"Auto-responding to prompt: {prompt_text} -> {response}")
            await self.send_input(response)
            return response

    # Unknown prompt - request user intervention via WebSocket
    await self.request_user_input(prompt_text)
    return await self.wait_for_user_response()
```

### 4. Resource Management

```python
class AgentResourceLimits:
    """Resource limits for Claude Code agents"""

    MAX_MEMORY_MB = 2048
    MAX_CPU_PERCENT = 80
    MAX_EXECUTION_TIME_SECONDS = 3600  # 1 hour
    MAX_FILE_OPERATIONS = 1000

    @staticmethod
    async def enforce_limits(process: asyncio.subprocess.Process) -> None:
        """Enforce resource limits on subprocess"""
        # Use resource.setrlimit on Unix systems
        import resource

        # Memory limit
        resource.prlimit(
            process.pid,
            resource.RLIMIT_AS,
            (AgentResourceLimits.MAX_MEMORY_MB * 1024 * 1024, resource.RLIM_INFINITY)
        )

        # CPU time limit
        resource.prlimit(
            process.pid,
            resource.RLIMIT_CPU,
            (AgentResourceLimits.MAX_EXECUTION_TIME_SECONDS, resource.RLIM_INFINITY)
        )
```

## Task Execution Strategies

### Strategy 1: Top N Tasks
```python
async def execute_top_n_tasks(agent: ClaudeCodeAgent, n: int = 20) -> None:
    """Execute top N priority tasks from TODO.md"""
    tasks = await load_todo_tasks()
    top_tasks = sorted(tasks, key=lambda t: t.priority)[:n]

    for task in top_tasks:
        await agent.start(task.description)
        await agent.wait_for_completion()
        await agent.stop()

        # Commit after each task
        await git_commit(f"feat: {task.description}")
```

### Strategy 2: Bottom N Tasks
```python
async def execute_bottom_n_tasks(agent: ClaudeCodeAgent, n: int = 20) -> None:
    """Execute bottom N priority tasks from TODO.md"""
    tasks = await load_todo_tasks()
    bottom_tasks = sorted(tasks, key=lambda t: t.priority, reverse=True)[:n]

    for task in bottom_tasks:
        await agent.start(task.description)
        await agent.wait_for_completion()
        await agent.stop()
        await git_commit(f"feat: {task.description}")
```

### Strategy 3: Random N Tasks
```python
import random

async def execute_random_n_tasks(agent: ClaudeCodeAgent, n: int = 20) -> None:
    """Execute random N tasks from TODO.md"""
    tasks = await load_todo_tasks()
    random_tasks = random.sample(tasks, min(n, len(tasks)))

    for task in random_tasks:
        await agent.start(task.description)
        await agent.wait_for_completion()
        await agent.stop()
        await git_commit(f"feat: {task.description}")
```

## Integration with WebSocket

### Real-time Output Streaming

```python
from src.pokertool.api_improve import terminal_manager

async def stream_output_to_frontend(
    agent: ClaudeCodeAgent,
    agent_id: str
) -> None:
    """Stream Claude Code output to frontend terminal"""
    while agent.is_running():
        output = await agent.read_output()
        if output:
            # Send to frontend WebSocket
            await terminal_manager.send_output(agent_id, output)
        await asyncio.sleep(0.05)  # 50ms polling
```

### Status Updates

```python
async def update_agent_status(
    agent_id: str,
    status: str,
    task_info: Optional[str] = None
) -> None:
    """Update agent status on frontend"""
    await terminal_manager.send_status(agent_id, status, task_info)

    # Also update agent state in database
    await db.update_agent_status(agent_id, status, task_info)
```

## Error Recovery

### Automatic Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def execute_task_with_retry(
    agent: ClaudeCodeAgent,
    task: str
) -> None:
    """Execute task with automatic retry on failure"""
    try:
        await agent.start(task)
        result = await agent.wait_for_completion(timeout=1800)  # 30 min

        if not result.success:
            raise TaskExecutionError(result.error)

    except asyncio.TimeoutError:
        await agent.stop(graceful=False)
        raise TaskTimeoutError(f"Task timed out: {task}")
```

### Fallback Strategies

```python
async def execute_with_fallback(
    task: str,
    primary_provider: str = "claude-code",
    fallback_provider: str = "anthropic"
) -> None:
    """Execute task with fallback to alternative provider"""
    try:
        # Try primary provider (Claude Code)
        agent = ClaudeCodeAgent(agent_id, workspace_dir)
        await agent.start(task)
        result = await agent.wait_for_completion()
        return result

    except Exception as e:
        logger.warning(f"Primary provider failed: {e}. Falling back...")

        # Fallback to Anthropic API
        from src.pokertool.ai_providers.anthropic_provider import AnthropicProvider
        provider = AnthropicProvider(api_key=os.getenv("ANTHROPIC_API_KEY"))
        return await provider.execute_task(task)
```

## Security Considerations

### 1. Sandbox Execution

```python
# Run Claude Code in sandboxed environment
async def create_sandboxed_agent(agent_id: str) -> ClaudeCodeAgent:
    """Create agent with sandboxed workspace"""
    sandbox_dir = f"/tmp/claude-code-sandbox-{agent_id}"
    os.makedirs(sandbox_dir, exist_ok=True)

    # Copy only necessary files
    shutil.copytree(
        "/path/to/repo",
        sandbox_dir,
        ignore=shutil.ignore_patterns(".git", "node_modules", "*.pyc")
    )

    agent = ClaudeCodeAgent(agent_id, sandbox_dir)
    return agent
```

### 2. File Access Restrictions

```python
ALLOWED_FILE_PATTERNS = [
    "src/**/*.py",
    "src/**/*.ts",
    "src/**/*.tsx",
    "docs/**/*.md",
    "tests/**/*.py"
]

FORBIDDEN_FILE_PATTERNS = [
    ".env",
    "**/*credentials*",
    "**/*secret*",
    "**/*.key",
    ".git/config"
]

def validate_file_access(file_path: str) -> bool:
    """Validate if Claude Code should have access to file"""
    # Check against allowed patterns
    if not any(fnmatch.fnmatch(file_path, pattern) for pattern in ALLOWED_FILE_PATTERNS):
        return False

    # Check against forbidden patterns
    if any(fnmatch.fnmatch(file_path, pattern) for pattern in FORBIDDEN_FILE_PATTERNS):
        return False

    return True
```

## Performance Optimization

### 1. Parallel Execution

```python
async def run_agents_in_parallel(tasks: List[str]) -> List[Any]:
    """Run multiple Claude Code agents in parallel"""
    agents = [
        ClaudeCodeAgent(f"agent-{i}", workspace_dir)
        for i in range(3)
    ]

    # Distribute tasks among agents
    task_chunks = [tasks[i::3] for i in range(3)]

    # Execute in parallel
    results = await asyncio.gather(*[
        execute_task_list(agent, chunk)
        for agent, chunk in zip(agents, task_chunks)
    ])

    return results
```

### 2. Caching and Deduplication

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def get_task_hash(task: str) -> str:
    """Generate hash for task to detect duplicates"""
    return hashlib.sha256(task.encode()).hexdigest()

async def execute_deduplicated_tasks(tasks: List[str]) -> None:
    """Execute tasks, skipping duplicates"""
    seen_hashes = set()

    for task in tasks:
        task_hash = get_task_hash(task)
        if task_hash in seen_hashes:
            logger.info(f"Skipping duplicate task: {task[:50]}...")
            continue

        seen_hashes.add(task_hash)
        await execute_task(task)
```

## Monitoring and Logging

### Comprehensive Logging

```python
import logging
from datetime import datetime

class AgentLogger:
    """Structured logging for Claude Code agents"""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.logger = logging.getLogger(f"agent.{agent_id}")

    def log_task_start(self, task: str) -> None:
        self.logger.info({
            "event": "task_start",
            "agent_id": self.agent_id,
            "task": task,
            "timestamp": datetime.utcnow().isoformat()
        })

    def log_task_complete(self, task: str, duration_ms: float) -> None:
        self.logger.info({
            "event": "task_complete",
            "agent_id": self.agent_id,
            "task": task,
            "duration_ms": duration_ms,
            "timestamp": datetime.utcnow().isoformat()
        })

    def log_error(self, error: Exception, context: Dict[str, Any]) -> None:
        self.logger.error({
            "event": "error",
            "agent_id": self.agent_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "timestamp": datetime.utcnow().isoformat()
        })
```

## Testing

### Unit Tests

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_claude_code_agent_start():
    """Test starting Claude Code agent"""
    agent = ClaudeCodeAgent("test-agent", "/tmp/test")

    with patch("asyncio.create_subprocess_exec") as mock_subprocess:
        mock_process = AsyncMock()
        mock_subprocess.return_value = mock_process

        await agent.start("Test task")

        assert agent.process == mock_process
        mock_subprocess.assert_called_once()

@pytest.mark.asyncio
async def test_claude_code_agent_error_handling():
    """Test error handling in Claude Code agent"""
    agent = ClaudeCodeAgent("test-agent", "/tmp/test")
    agent.process = AsyncMock()
    agent.process.stderr.readline.return_value = b"Error: Test error\n"

    errors = []
    agent.handle_error = lambda e: errors.append(e)

    await agent.monitor_process()

    assert len(errors) > 0
    assert "Test error" in errors[0]
```

## References

- [FastAPI WebSocket Documentation](https://fastapi.tiangolo.com/advanced/websockets/)
- [asyncio Subprocess Documentation](https://docs.python.org/3/library/asyncio-subprocess.html)
- [xterm.js Documentation](https://xtermjs.org/docs/)
- [Process Management Best Practices](https://www.python.org/dev/peps/pep-3143/)

## Conclusion

Integrating Claude Code CLI requires careful handling of:
1. **Subprocess lifecycle** - Start, monitor, stop gracefully
2. **Interactive prompts** - Auto-respond or request user input
3. **Error recovery** - Retry logic and fallback strategies
4. **Resource limits** - Prevent runaway processes
5. **Security** - Sandbox execution and file access restrictions
6. **Performance** - Parallel execution and caching
7. **Monitoring** - Comprehensive logging and status updates

Follow these best practices to create a robust, production-ready AI agent system.
