# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/controller/mcp/deleteMcpServer.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { StringRequest } from "@shared/proto/cline/common"
import { McpServers } from "@shared/proto/cline/mcp"
import { convertMcpServersToProtoMcpServers } from "../../../shared/proto-conversions/mcp/mcp-server-conversion"
import type { Controller } from "../index"

/**
 * Deletes an MCP server
 * @param controller The controller instance
 * @param request The delete server request
 * @returns The list of remaining MCP servers after deletion
 */
export async function deleteMcpServer(controller: Controller, request: StringRequest): Promise<McpServers> {
    try {
        // Call the RPC variant to delete the server and get updated server list
        const mcpServers = (await controller.mcpHub?.deleteServerRPC(request.value)) || []

        // Convert application types to protobuf types
        const protoServers = convertMcpServersToProtoMcpServers(mcpServers)

        return McpServers.create({ mcpServers: protoServers })
    } catch (error) {
        console.error(`Failed to delete MCP server: ${error}`)
        throw error
    }
}
