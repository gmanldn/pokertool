# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/integrations/claude-code/types.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import type { Anthropic } from "@anthropic-ai/sdk"

type InitMessage = {
    type: "system"
    subtype: "init"
    session_id: string
    tools: string[]
    mcp_servers: string[]
    apiKeySource: "none" | "/login managed key" | string
}

type AssistantMessage = {
    type: "assistant"
    message: Anthropic.Messages.Message
    session_id: string
}

type ErrorMessage = {
    type: "error"
}

type ResultMessage = {
    type: "result"
    subtype: "success"
    total_cost_usd: number
    is_error: boolean
    duration_ms: number
    duration_api_ms: number
    num_turns: number
    result: string
    session_id: string
}

export type ClaudeCodeMessage = InitMessage | AssistantMessage | ErrorMessage | ResultMessage
