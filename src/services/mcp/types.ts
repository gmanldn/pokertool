// POKERTOOL-HEADER-START
// ---
// schema: pokerheader.v1
// project: pokertool
// file: src/services/mcp/types.ts
// version: v28.0.0
// last_commit: '2025-09-23T08:41:38+01:00'
// fixes:
// - date: '2025-09-25'
//   summary: Enhanced enterprise documentation and comprehensive unit tests added
// ---
// POKERTOOL-HEADER-END
import { Client } from "@modelcontextprotocol/sdk/client/index.js"
import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js"
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js"
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js"
import { McpServer } from "@shared/mcp"
import { z } from "zod"
import { ServerConfigSchema } from "./schemas"

export type Transport = StdioClientTransport | SSEClientTransport | StreamableHTTPClientTransport

export type McpConnection = {
    server: McpServer
    client: Client
    transport: Transport
}

export type McpTransportType = "stdio" | "sse" | "http"

export type McpServerConfig = z.infer<typeof ServerConfigSchema>
