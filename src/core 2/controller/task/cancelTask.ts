# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/controller/task/cancelTask.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { Empty, EmptyRequest } from "@shared/proto/cline/common"
import { Controller } from ".."

/**
 * Cancel the currently running task
 * @param controller The controller instance
 * @param _request The empty request
 * @returns Empty response
 */
export async function cancelTask(controller: Controller, _request: EmptyRequest): Promise<Empty> {
	await controller.cancelTask()
	return Empty.create()
}
