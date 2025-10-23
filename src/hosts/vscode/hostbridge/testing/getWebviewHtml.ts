// POKERTOOL-HEADER-START
// ---
// schema: pokerheader.v1
// project: pokertool
// file: src/hosts/vscode/hostbridge/testing/getWebviewHtml.ts
// version: v28.0.0
// last_commit: '2025-09-23T08:41:38+01:00'
// fixes:
// - date: '2025-09-25'
//   summary: Enhanced enterprise documentation and comprehensive unit tests added
// ---
// POKERTOOL-HEADER-END
import { GetWebviewHtmlRequest, GetWebviewHtmlResponse } from "@/shared/proto/index.host"

export async function getWebviewHtml(_: GetWebviewHtmlRequest): Promise<GetWebviewHtmlResponse> {
	throw new Error("Unimplemented")
}
