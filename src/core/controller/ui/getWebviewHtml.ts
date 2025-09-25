# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/controller/ui/getWebviewHtml.ts
# version: v20.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { EmptyRequest, String } from "@shared/proto/cline/common"
import { WebviewProvider } from "@/core/webview"
import type { Controller } from "../index"

/**
 * Returns the HTML content of the webview.
 *
 * This is only used by the standalone service. The Vscode extension gets the HTML directly from the webview when it
 * resolved through `resolveWebviewView()`.
 */
export async function getWebviewHtml(_controller: Controller, _: EmptyRequest): Promise<String> {
	const webviewProvider = WebviewProvider.getLastActiveInstance()
	if (!webviewProvider) {
		throw new Error("No active webview")
	}
	return Promise.resolve(String.create({ value: webviewProvider.getHtmlContent() }))
}
