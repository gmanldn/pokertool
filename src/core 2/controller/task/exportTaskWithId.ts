# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/controller/task/exportTaskWithId.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { Empty, StringRequest } from "@shared/proto/cline/common"
import { Controller } from ".."

/**
 * Exports a task with the given ID to markdown
 * @param controller The controller instance
 * @param request The request containing the task ID in the value field
 * @returns Empty response
 */
export async function exportTaskWithId(controller: Controller, request: StringRequest): Promise<Empty> {
	try {
		if (request.value) {
			await controller.exportTaskWithId(request.value)
		}
		return Empty.create()
	} catch (error) {
		// Log the error but allow it to propagate for proper gRPC error handling
		console.error(`Error exporting task with ID ${request.value}:`, error)
		throw error
	}
}
