// POKERTOOL-HEADER-START
// ---
// schema: pokerheader.v1
// project: pokertool
// file: src/core/controller/web/openInBrowser.ts
// version: v28.0.0
// last_commit: '2025-09-23T08:41:38+01:00'
// fixes:
// - date: '2025-09-25'
//   summary: Enhanced enterprise documentation and comprehensive unit tests added
// ---
// POKERTOOL-HEADER-END
import { Empty, StringRequest } from "@shared/proto/cline/common"
import { openExternal } from "@utils/env"
import { Controller } from ".."

/**
 * Opens a URL in the user's default browser
 * @param controller The controller instance
 * @param request The URL to open
 * @returns Empty response since the client doesn't need a return value
 */
export async function openInBrowser(_controller: Controller, request: StringRequest): Promise<Empty> {
	try {
		if (request.value) {
			await openExternal(request.value)
		}
		return Empty.create()
	} catch (error) {
		console.error("Error opening URL in browser:", error)
		return Empty.create()
	}
}
