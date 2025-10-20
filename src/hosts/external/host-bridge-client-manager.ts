# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/hosts/external/host-bridge-client-manager.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import {
    DiffServiceClientInterface,
    EnvServiceClientInterface,
    WindowServiceClientInterface,
    WorkspaceServiceClientInterface,
} from "@generated/hosts/host-bridge-client-types"
import {
    DiffServiceClientImpl,
    EnvServiceClientImpl,
    WindowServiceClientImpl,
    WorkspaceServiceClientImpl,
} from "@generated/hosts/standalone/host-bridge-clients"
import { HostBridgeClientProvider } from "@/hosts/host-provider-types"
import { HOSTBRIDGE_PORT } from "@/standalone/hostbridge-client"

/**
 * Manager to hold the gRPC clients for the host bridge. The clients should be re-used to avoid
 * creating a new TCP connection every time a rpc is made.
 */
export class ExternalHostBridgeClientManager implements HostBridgeClientProvider {
    workspaceClient: WorkspaceServiceClientInterface
    envClient: EnvServiceClientInterface
    windowClient: WindowServiceClientInterface
    diffClient: DiffServiceClientInterface

    constructor() {
        const address = process.env.HOST_BRIDGE_ADDRESS || `localhost:${HOSTBRIDGE_PORT}`

        this.workspaceClient = new WorkspaceServiceClientImpl(address)
        this.envClient = new EnvServiceClientImpl(address)
        this.windowClient = new WindowServiceClientImpl(address)
        this.diffClient = new DiffServiceClientImpl(address)
    }
}
