# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/controller/task/newTask.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { Empty } from "@shared/proto/cline/common"
import { NewTaskRequest } from "@shared/proto/cline/task"
import { Controller } from ".."

/**
 * Creates a new task with the given text and optional images
 * @param controller The controller instance
 * @param request The new task request containing text and optional images
 * @returns Empty response
 */
export async function newTask(controller: Controller, request: NewTaskRequest): Promise<Empty> {
	await controller.initTask(request.text, request.images, request.files)
	return Empty.create()
}
