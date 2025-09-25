# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/controller/mcp/updateMcpTimeout.ts
# version: v20.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { McpServers, UpdateMcpTimeoutRequest } from "@shared/proto/cline/mcp"
import { convertMcpServersToProtoMcpServers } from "@/shared/proto-conversions/mcp/mcp-server-conversion"
import { Controller } from ".."

/**
 * Updates the timeout configuration for an MCP server.
 * @param controller - The Controller instance
 * @param request - Contains server name and timeout value
 * @returns Array of updated McpServer objects
 */
export async function updateMcpTimeout(controller: Controller, request: UpdateMcpTimeoutRequest): Promise<McpServers> {
	try {
		if (request.serverName && typeof request.serverName === "string" && typeof request.timeout === "number") {
			const mcpServers = await controller.mcpHub?.updateServerTimeoutRPC(request.serverName, request.timeout)
			const convertedMcpServers = convertMcpServersToProtoMcpServers(mcpServers)
			console.log("convertedMcpServers", convertedMcpServers)
			return McpServers.create({ mcpServers: convertedMcpServers })
		} else {
			console.error("Server name and timeout are required")
			throw new Error("Server name and timeout are required")
		}
	} catch (error) {
		console.error(`Failed to update timeout for server ${request.serverName}:`, error)
		throw error
	}
}
