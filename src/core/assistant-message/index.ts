// POKERTOOL-HEADER-START
// ---
// schema: pokerheader.v1
// project: pokertool
// file: src/core/assistant-message/index.ts
// version: v28.0.0
// last_commit: '2025-09-23T08:41:38+01:00'
// fixes:
// - date: '2025-09-25'
//   summary: Enhanced enterprise documentation and comprehensive unit tests added
// ---
// POKERTOOL-HEADER-END
import { ClineDefaultTool } from "@shared/tools"
export type AssistantMessageContent = TextContent | ToolUse

export { parseAssistantMessageV2 } from "./parse-assistant-message"

export interface TextContent {
    type: "text"
    content: string
    partial: boolean
}

export const toolParamNames = [
    "command",
    "requires_approval",
    "path",
    "content",
    "diff",
    "regex",
    "file_pattern",
    "recursive",
    "action",
    "url",
    "coordinate",
    "text",
    "server_name",
    "tool_name",
    "arguments",
    "uri",
    "question",
    "options",
    "response",
    "result",
    "context",
    "title",
    "what_happened",
    "steps_to_reproduce",
    "api_request_output",
    "additional_context",
    "needs_more_exploration",
    "task_progress",
    "timeout",
] as const

export type ToolParamName = (typeof toolParamNames)[number]

export interface ToolUse {
    type: "tool_use"
    name: ClineDefaultTool // id of the tool being used
    // params is a partial record, allowing only some or none of the possible parameters to be used
    params: Partial<Record<ToolParamName, string>>
    partial: boolean
}
