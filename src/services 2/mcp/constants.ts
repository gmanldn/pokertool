# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/services/mcp/constants.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
/**
 * Default timeout for internal MCP data requests in milliseconds.
 * This is not the same as the user facing timeout stored as DEFAULT_MCP_TIMEOUT_SECONDS.
 */
export const DEFAULT_REQUEST_TIMEOUT_MS = 5000

/**
 * Custom error message for better user feedback when server type validation fails.
 */
export const TYPE_ERROR_MESSAGE = "Server type must be one of: 'stdio', 'sse', or 'streamableHttp'"
