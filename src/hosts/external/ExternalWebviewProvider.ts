# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/hosts/external/ExternalWebviewProvider.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import * as vscode from "vscode"
import { WebviewProvider } from "@/core/webview"
import { WebviewProviderType } from "@/shared/webview/types"

export class ExternalWebviewProvider extends WebviewProvider {
    // This hostname cannot be changed without updating the external webview handler.
    private RESOURCE_HOSTNAME: string = "internal.resources"

    constructor(context: vscode.ExtensionContext, providerType: WebviewProviderType) {
        super(context, providerType)
    }

    override getWebviewUrl(path: string) {
        const url = new URL(`https://${this.RESOURCE_HOSTNAME}/`)
        url.pathname = path
        return url.toString()
    }
    override getCspSource() {
        return `'self' https://${this.RESOURCE_HOSTNAME}`
    }
    override isVisible() {
        return true
    }
    protected override isActive(): boolean {
        return true
    }
}
