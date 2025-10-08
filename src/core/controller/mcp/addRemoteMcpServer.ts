# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/controller/mcp/addRemoteMcpServer.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import type { AddRemoteMcpServerRequest } from "@shared/proto/cline/mcp"
import { McpServers } from "@shared/proto/cline/mcp"
import { convertMcpServersToProtoMcpServers } from "@/shared/proto-conversions/mcp/mcp-server-conversion"
import type { Controller } from "../index"

/**
 * Adds a new remote MCP server via gRPC
 * @param controller The controller instance
 * @param request The request containing server name and URL
 * @returns An array of McpServer objects
 */
export async function addRemoteMcpServer(controller: Controller, request: AddRemoteMcpServerRequest): Promise<McpServers> {
    try {
        // Validate required fields
        if (!request.serverName) {
            throw new Error("Server name is required")
        }
        if (!request.serverUrl) {
            throw new Error("Server URL is required")
        }

        // Call the McpHub method to add the remote server
        const servers = await controller.mcpHub?.addRemoteServer(request.serverName, request.serverUrl)

        const protoServers = convertMcpServersToProtoMcpServers(servers)

        return McpServers.create({ mcpServers: protoServers })
    } catch (error) {
        console.error(`Failed to add remote MCP server ${request.serverName}:`, error)

        throw error
    }
}
