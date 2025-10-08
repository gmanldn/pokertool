# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/controller/mcp/restartMcpServer.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { StringRequest } from "@shared/proto/cline/common"
import { McpServers } from "@shared/proto/cline/mcp"
import { convertMcpServersToProtoMcpServers } from "@shared/proto-conversions/mcp/mcp-server-conversion"
import type { Controller } from "../index"

/**
 * Restarts an MCP server connection
 * @param controller The controller instance
 * @param request The request containing the server name
 * @returns The updated list of MCP servers
 */
export async function restartMcpServer(controller: Controller, request: StringRequest): Promise<McpServers> {
	try {
		const mcpServers = await controller.mcpHub?.restartConnectionRPC(request.value)

		// Convert from McpServer[] to ProtoMcpServer[] ensuring all required fields are set
		const protoServers = convertMcpServersToProtoMcpServers(mcpServers)

		return McpServers.create({ mcpServers: protoServers })
	} catch (error) {
		console.error(`Failed to restart MCP server ${request.value}:`, error)
		throw error
	}
}
