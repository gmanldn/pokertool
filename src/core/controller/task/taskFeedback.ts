# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/controller/task/taskFeedback.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { Empty, StringRequest } from "@shared/proto/cline/common"
import { telemetryService } from "@/services/telemetry"
import { Controller } from ".."

/**
 * Handles task feedback submission (thumbs up/down)
 * @param controller The controller instance
 * @param request The StringRequest containing the feedback type ("thumbs_up" or "thumbs_down") in the value field
 * @returns Empty response
 */
export async function taskFeedback(controller: Controller, request: StringRequest): Promise<Empty> {
    if (!request.value) {
        console.warn("taskFeedback: Missing feedback type value")
        return Empty.create()
    }

    try {
        if (controller.task?.ulid) {
            telemetryService.captureTaskFeedback(controller.task.ulid, request.value as any)
        } else {
            console.warn("taskFeedback: No active task to receive feedback")
        }
    } catch (error) {
        console.error("Error in taskFeedback handler:", error)
    }

    return Empty.create()
}
