// POKERTOOL-HEADER-START
// ---
// schema: pokerheader.v1
// project: pokertool
// file: src/hosts/vscode/hostbridge/client/host-grpc-client.ts
// version: v28.0.0
// last_commit: '2025-09-23T08:41:38+01:00'
// fixes:
// - date: '2025-09-25'
//   summary: Enhanced enterprise documentation and comprehensive unit tests added
// ---
// POKERTOOL-HEADER-END
import { createGrpcClient } from "@hosts/vscode/hostbridge/client/host-grpc-client-base"
import * as host from "@shared/proto/index.host"
import { HostBridgeClientProvider } from "@/hosts/host-provider-types"

export const vscodeHostBridgeClient: HostBridgeClientProvider = {
	workspaceClient: createGrpcClient(host.WorkspaceServiceDefinition),
	envClient: createGrpcClient(host.EnvServiceDefinition),
	windowClient: createGrpcClient(host.WindowServiceDefinition),
	diffClient: createGrpcClient(host.DiffServiceDefinition),
}
