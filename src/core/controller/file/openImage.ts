# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/controller/file/openImage.ts
# version: v20.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { openImage as openImageIntegration } from "@integrations/misc/open-file"
import { Empty, StringRequest } from "@shared/proto/cline/common"
import { Controller } from ".."

/**
 * Opens an image in the system viewer
 * @param controller The controller instance
 * @param request The request message containing the image path or data URI in the 'value' field
 * @returns Empty response
 */
export async function openImage(_controller: Controller, request: StringRequest): Promise<Empty> {
	if (request.value) {
		await openImageIntegration(request.value)
	}
	return Empty.create()
}
