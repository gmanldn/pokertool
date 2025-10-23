// POKERTOOL-HEADER-START
// ---
// schema: pokerheader.v1
// project: pokertool
// file: src/test/host-provider-test-utils.ts
// version: v28.0.0
// last_commit: '2025-09-23T08:41:38+01:00'
// fixes:
// - date: '2025-09-25'
//   summary: Enhanced enterprise documentation and comprehensive unit tests added
// ---
// POKERTOOL-HEADER-END
import { DiffViewProviderCreator, HostProvider, WebviewProviderCreator } from "@/hosts/host-provider"
import { HostBridgeClientProvider } from "@/hosts/host-provider-types"
import { vscodeHostBridgeClient } from "@/hosts/vscode/hostbridge/client/host-grpc-client"

/**
 * Initializes the HostProvider with test defaults.
 * This is a common setup used across multiple test files.
 *
 * @param options Optional overrides for the default test configuration
 */
export function setVscodeHostProviderMock(options?: {
    webviewProviderCreator?: WebviewProviderCreator
    diffViewProviderCreator?: DiffViewProviderCreator
    hostBridgeClient?: HostBridgeClientProvider
    logToChannel?: (message: string) => void
    getCallbackUri?: () => Promise<string>
    getBinaryLocation?: (name: string) => Promise<string>
    extensionFsPath?: string
    globalStorageFsPath?: string
}) {
    HostProvider.reset()
    HostProvider.initialize(
        options?.webviewProviderCreator ?? (((_) => {}) as WebviewProviderCreator),
        options?.diffViewProviderCreator ?? ((() => {}) as DiffViewProviderCreator),
        options?.hostBridgeClient ?? vscodeHostBridgeClient,
        options?.logToChannel ?? ((_) => {}),
        options?.getCallbackUri ?? (async () => "http://example.com:1234/"),
        options?.getBinaryLocation ?? (async (n) => `/mock/path/to/binary/${n}`),
        options?.extensionFsPath ?? "/mock/path/to/extension",
        options?.globalStorageFsPath ?? "/mock/path/to/globalstorage",
    )
}
