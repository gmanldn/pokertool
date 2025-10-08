# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/shared/McpDisplayMode.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
/**
 * Represents the different display modes available for MCP responses
 */
export type McpDisplayMode = "rich" | "plain" | "markdown"

/**
 * Default display mode for MCP responses
 */
export const DEFAULT_MCP_DISPLAY_MODE: McpDisplayMode = "plain"
