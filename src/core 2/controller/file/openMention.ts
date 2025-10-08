# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/controller/file/openMention.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { Empty, StringRequest } from "@shared/proto/cline/common"
import { openMention as coreOpenMention } from "../../mentions"
import { Controller } from ".."

/**
 * Opens a mention (file path, problem, terminal, or URL)
 * @param controller The controller instance
 * @param request The string request containing the mention text
 * @returns Empty response
 */
export async function openMention(_controller: Controller, request: StringRequest): Promise<Empty> {
	coreOpenMention(request.value)
	return Empty.create()
}
