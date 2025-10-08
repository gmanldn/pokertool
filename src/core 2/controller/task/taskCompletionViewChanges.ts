# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/controller/task/taskCompletionViewChanges.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { Empty, Int64Request } from "@shared/proto/cline/common"
import { Controller } from ".."

/**
 * Shows task completion changes in a diff view
 * @param controller The controller instance
 * @param request The request containing the timestamp of the message
 * @returns Empty response
 */
export async function taskCompletionViewChanges(controller: Controller, request: Int64Request): Promise<Empty> {
	try {
		if (request.value && controller.task) {
			// presentMultifileDiff is optional on ICheckpointManager, so capture then optionally invoke
			await controller.task.checkpointManager?.presentMultifileDiff?.(request.value, true)
		}
		return Empty.create()
	} catch (error) {
		console.error("Error in taskCompletionViewChanges handler:", error)
		throw error
	}
}
