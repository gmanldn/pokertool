// POKERTOOL-HEADER-START
// ---
// schema: pokerheader.v1
// project: pokertool
// file: src/core/controller/mcp/getLatestMcpServers.ts
// version: v28.0.0
// last_commit: '2025-09-23T08:41:38+01:00'
// fixes:
// - date: '2025-09-25'
//   summary: Enhanced enterprise documentation and comprehensive unit tests added
// ---
// POKERTOOL-HEADER-END
import type { Empty } from "@shared/proto/cline/common"
import { McpServers } from "@shared/proto/cline/mcp"
import { convertMcpServersToProtoMcpServers } from "@/shared/proto-conversions/mcp/mcp-server-conversion"
import type { Controller } from "../index"

/**
 * RPC handler for getting the latest MCP servers
 * @param controller The controller instance
 * @param _request Empty request
 * @returns McpServers response with list of all MCP servers
 */
export async function getLatestMcpServers(controller: Controller, _request: Empty): Promise<McpServers> {
	try {
		// Get sorted servers from mcpHub using the RPC variant
		const mcpServers = (await controller.mcpHub?.getLatestMcpServersRPC()) || []

		// Convert to proto format
		const protoServers = convertMcpServersToProtoMcpServers(mcpServers)

		return McpServers.create({ mcpServers: protoServers })
	} catch (error) {
		console.error("Error fetching latest MCP servers:", error)
		throw error
	}
}
