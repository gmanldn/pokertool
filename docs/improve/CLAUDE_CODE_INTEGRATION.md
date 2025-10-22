# Claude Code CLI Integration Guide

Research and best practices for spawning Claude Code as subprocess and handling responses.

## Overview

Claude Code CLI provides command-line interaction with Claude AI. This guide covers subprocess management and response parsing.

## Authentication

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Best Practices

1. **Always set timeouts** - Prevent hanging on network issues
2. **Use --non-interactive** - Avoid blocking on prompts  
3. **Parse JSON output** - More reliable than text
4. **Handle stderr** - Important errors
5. **Clean up processes** - Terminate on errors
6. **Rate limiting** - Respect API limits

## Example

```python
process = await asyncio.create_subprocess_exec(
    "claude-code",
    "--non-interactive",
    stdin=asyncio.subprocess.PIPE,
    stdout=asyncio.subprocess.PIPE,
    timeout=300
)
```

See `src/pokertool/ai_providers/claude_code_provider.py` for full implementation.
