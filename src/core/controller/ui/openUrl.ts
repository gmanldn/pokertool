# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/controller/ui/openUrl.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import type { StringRequest } from "@shared/proto/cline/common"
import { Empty } from "@shared/proto/cline/common"
import { openUrlInBrowser } from "../../../utils/github-url-utils"
import type { Controller } from "../index"

/**
 * Opens a URL in the default browser
 * @param controller The controller instance
 * @param request The URL to open
 * @returns Empty response
 */
export async function openUrl(_controller: Controller, request: StringRequest): Promise<Empty> {
	try {
		await openUrlInBrowser(request.value)
		return Empty.create({})
	} catch (error) {
		console.error(`Failed to open URL: ${error}`)
		throw error
	}
}
