# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/task/tools/utils/ToolDisplayUtils.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { ToolParamName, ToolUse } from "@core/assistant-message"
import type { ToolExecutorCoordinator } from "../ToolExecutorCoordinator"
import { removeClosingTag } from "./ToolConstants"

/**
 * Utility functions for tool display and formatting
 */
export class ToolDisplayUtils {
	/**
	 * Generate a descriptive string for a tool execution
	 * @param block - The tool use block
	 * @param coordinator - Optional tool coordinator to get description from tool handler
	 */
	static getToolDescription(block: ToolUse, coordinator?: ToolExecutorCoordinator): string {
		// Try to get description from the tool handler first
		if (coordinator) {
			const handler = coordinator.getHandler(block.name)
			if (handler) {
				return handler.getDescription(block)
			}
		}

		return `[${block.name}]`
	}

	/**
	 * Remove partial closing tag from tool parameter text
	 * If block is partial, remove partial closing tag so it's not presented to user
	 */
	static removeClosingTag(block: ToolUse, tag: ToolParamName, text?: string): string {
		return removeClosingTag(block, tag, text)
	}
}
