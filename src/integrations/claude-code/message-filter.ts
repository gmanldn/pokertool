# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/integrations/claude-code/message-filter.ts
# version: v20.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import type { Anthropic } from "@anthropic-ai/sdk"

/**
 * Filters out image blocks from messages since Claude Code doesn't support images.
 * Replaces image blocks with text placeholders similar to how VSCode LM provider handles it.
 */
export function filterMessagesForClaudeCode(messages: Anthropic.Messages.MessageParam[]): Anthropic.Messages.MessageParam[] {
	return messages.map((message) => {
		// Handle simple string messages
		if (typeof message.content === "string") {
			return message
		}

		// Handle complex message structures
		const filteredContent = message.content.map((block) => {
			if (block.type === "image") {
				// Replace image blocks with text placeholders
				const sourceType = block.source?.type || "unknown"
				const mediaType = block.source?.media_type || "unknown"
				return {
					type: "text" as const,
					text: `[Image (${sourceType}): ${mediaType} not supported by Claude Code]`,
				}
			}
			return block
		})

		return {
			...message,
			content: filteredContent,
		}
	})
}
