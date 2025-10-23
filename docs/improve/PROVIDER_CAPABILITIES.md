# AI Provider Capabilities Matrix

This document outlines the capabilities and limitations of each AI provider supported by the Improve tab.

## Overview

| Provider | Code Execution | File Editing | Testing | Streaming | Function Calling | Cost | Speed |
|----------|---------------|--------------|---------|-----------|------------------|------|-------|
| Claude Code | ✅ Full | ✅ Full | ✅ Full | ❌ No | ⚠️ Limited | $$ | Fast |
| Anthropic API | ⚠️ Limited | ✅ Full | ⚠️ Limited | ✅ Yes | ⚠️ Limited | $$ | Fast |
| OpenRouter | ⚠️ Limited | ✅ Full | ⚠️ Limited | ✅ Yes | ⚠️ Limited | $-$$$ | Variable |
| OpenAI GPT-4 | ⚠️ Limited | ✅ Full | ⚠️ Limited | ✅ Yes | ✅ Full | $$$ | Medium |

## Detailed Capabilities

### Claude Code (Recommended)

**Best for:** Complete task automation, local development

**Capabilities:**
- ✅ **Code Execution**: Full subprocess management, can run commands
- ✅ **File Editing**: Direct file system access, can read/write/edit files
- ✅ **Testing**: Can run pytest, jest, and other test frameworks
- ✅ **Git Operations**: Can create commits, push, manage branches
- ✅ **Package Management**: Can install npm/pip packages
- ❌ **Streaming**: Response comes all at once
- ⚠️ **Function Calling**: Limited, uses command-line interface

**Limitations:**
- Requires Claude Code CLI installed
- Uses ANTHROPIC_API_KEY environment variable
- No streaming support
- Output parsing required

**Configuration:**
```python
from pokertool.ai_providers.claude_code_provider import ClaudeCodeProvider

provider = ClaudeCodeProvider(api_key="your-key")
await provider.initialize()
```

---

### Anthropic API (Claude 3.5 Sonnet)

**Best for:** Planning, code generation, high-quality responses

**Capabilities:**
- ✅ **Streaming**: Real-time response streaming
- ✅ **File Editing**: Can suggest file changes (manual application required)
- ✅ **Code Generation**: Excellent code quality
- ✅ **Planning**: Strong reasoning capabilities
- ⚠️ **Code Execution**: Cannot execute code directly
- ⚠️ **Testing**: Cannot run tests, only suggest them
- ⚠️ **Function Calling**: No native function calling

**Limitations:**
- Cannot execute code automatically
- Requires manual application of file changes
- Cannot run tests or git commands
- Best used with agentic wrapper

**Configuration:**
```python
from pokertool.ai_providers.anthropic_provider import AnthropicProvider

provider = AnthropicProvider(
    api_key="your-key",
    model="claude-3-5-sonnet-20241022"
)
await provider.initialize()
```

**API Limits:**
- 50 requests/minute
- 10,000 tokens/minute
- Rate limiting built-in

---

### OpenRouter

**Best for:** Multi-model access, cost optimization

**Capabilities:**
- ✅ **Multi-Model**: Access to Claude, GPT-4, and many others
- ✅ **Streaming**: Response streaming supported
- ✅ **File Editing**: Via model responses
- ✅ **Cost Control**: Choose cheaper models
- ⚠️ **Code Execution**: Model-dependent, generally limited
- ⚠️ **Consistency**: Varies by model selected

**Supported Models:**
- `anthropic/claude-3.5-sonnet` (recommended)
- `openai/gpt-4-turbo`
- `meta/llama-3-70b`
- Many more...

**Limitations:**
- Requires separate OpenRouter account
- Variable pricing by model
- Rate limits depend on model
- Quality varies by model

**Configuration:**
```python
from pokertool.ai_providers.openrouter_provider import OpenRouterProvider

provider = OpenRouterProvider(
    api_key="your-key",
    model="anthropic/claude-3.5-sonnet"
)
await provider.initialize()
```

---

### OpenAI (GPT-4 Turbo)

**Best for:** Function calling, structured output

**Capabilities:**
- ✅ **Function Calling**: Native function calling support
- ✅ **Streaming**: Response streaming
- ✅ **Code Generation**: Good code quality
- ✅ **Structured Output**: JSON mode, function schemas
- ⚠️ **Code Execution**: Cannot execute automatically
- ⚠️ **File Editing**: Via responses, not direct

**Function Calling Example:**
```python
functions = [
    {
        "name": "create_file",
        "description": "Create a new file",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"}
            }
        }
    }
]
```

**Limitations:**
- Higher cost than alternatives
- Context window smaller than Claude
- Cannot execute code directly

**Configuration:**
```python
from pokertool.ai_providers.openai_provider import OpenAIProvider

provider = OpenAIProvider(
    api_key="your-key",
    model="gpt-4-turbo-preview"
)
await provider.initialize()
```

**API Limits:**
- 60 requests/minute (tier 1)
- 3,500 tokens/minute
- Rate limiting built-in

---

## Provider Fallback Strategy

Recommended fallback chains:

### For Maximum Reliability:
```python
primary = ClaudeCodeProvider()
fallbacks = [
    AnthropicProvider(),
    OpenRouterProvider(model="anthropic/claude-3.5-sonnet"),
    OpenAIProvider()
]
```

### For Cost Optimization:
```python
primary = OpenRouterProvider(model="anthropic/claude-3.5-sonnet")
fallbacks = [
    OpenRouterProvider(model="meta/llama-3-70b"),  # Cheaper
    AnthropicProvider()  # High quality backup
]
```

### For Speed:
```python
primary = ClaudeCodeProvider()  # Fastest for execution
fallbacks = [
    AnthropicProvider()  # Fast API calls
]
```

---

## Feature Comparison Details

### Code Execution

| Provider | Direct Execution | Subprocess | Docker | Sandbox |
|----------|-----------------|------------|---------|---------|
| Claude Code | ✅ Yes | ✅ Yes | ⚠️ Manual | ✅ Yes |
| Anthropic | ❌ No | ❌ No | ❌ No | N/A |
| OpenRouter | Depends on model | ❌ No | ❌ No | N/A |
| OpenAI | ❌ No | ❌ No | ❌ No | N/A |

### File Operations

| Provider | Read | Write | Edit | Delete |
|----------|------|-------|------|--------|
| Claude Code | ✅ | ✅ | ✅ | ✅ |
| Anthropic | ⚠️ Suggests | ⚠️ Suggests | ⚠️ Suggests | ⚠️ Suggests |
| OpenRouter | ⚠️ Suggests | ⚠️ Suggests | ⚠️ Suggests | ⚠️ Suggests |
| OpenAI | ⚠️ Suggests | ⚠️ Suggests | ⚠️ Suggests | ⚠️ Suggests |

### Testing Capabilities

| Provider | Run Tests | Generate Tests | Parse Results | Coverage |
|----------|-----------|----------------|---------------|----------|
| Claude Code | ✅ | ✅ | ✅ | ✅ |
| Anthropic | ❌ | ✅ | ❌ | ❌ |
| OpenRouter | ❌ | ✅ | ❌ | ❌ |
| OpenAI | ❌ | ✅ | ❌ | ❌ |

---

## Cost Comparison (Approximate)

Based on Claude 3.5 Sonnet pricing (~$3/MTok input, $15/MTok output):

| Provider | Cost per Task | Cost per Hour | Notes |
|----------|---------------|---------------|-------|
| Claude Code | $0.05-0.10 | $3-6 | Includes execution overhead |
| Anthropic | $0.04-0.08 | $2.40-4.80 | Direct API, minimal overhead |
| OpenRouter | $0.04-0.20 | Variable | Depends on model selected |
| OpenAI | $0.08-0.15 | $4.80-9 | GPT-4 Turbo pricing |

*Note: Costs vary based on task complexity, code size, and iteration count.*

---

## Recommendations by Use Case

### Full Task Automation
**Primary:** Claude Code
**Fallback:** Anthropic API

### Code Review & Analysis
**Primary:** Anthropic API
**Fallback:** OpenAI GPT-4

### Cost-Sensitive Projects
**Primary:** OpenRouter (cheaper models)
**Fallback:** Anthropic API

### High-Throughput
**Primary:** Claude Code (parallel execution)
**Fallback:** OpenRouter (rate limits vary by model)

### Complex Planning
**Primary:** Anthropic API (best reasoning)
**Fallback:** OpenAI GPT-4

---

## Environment Variables

```bash
# Anthropic (for Claude Code and Anthropic API)
export ANTHROPIC_API_KEY="sk-ant-..."

# OpenAI
export OPENAI_API_KEY="sk-..."

# OpenRouter
export OPENROUTER_API_KEY="sk-or-..."
```

---

## Future Enhancements

Planned provider additions:
- Google Gemini Pro
- Mistral AI
- Cohere Command
- Local models (Ollama, LM Studio)

Planned features:
- Provider health monitoring
- Automatic model selection
- Cost optimization suggestions
- Performance analytics
