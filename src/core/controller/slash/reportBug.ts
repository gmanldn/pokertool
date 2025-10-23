// POKERTOOL-HEADER-START
// ---
// schema: pokerheader.v1
// project: pokertool
// file: src/core/controller/slash/reportBug.ts
// version: v28.0.0
// last_commit: '2025-09-23T08:41:38+01:00'
// fixes:
// - date: '2025-09-25'
//   summary: Enhanced enterprise documentation and comprehensive unit tests added
// ---
// POKERTOOL-HEADER-END
import { Empty, StringRequest } from "@shared/proto/cline/common"
import { Controller } from ".."

/**
 * Report bug slash command logic
 */
export async function reportBug(controller: Controller, _request: StringRequest): Promise<Empty> {
	await controller.task?.handleWebviewAskResponse("yesButtonClicked")
	return Empty.create()
}
