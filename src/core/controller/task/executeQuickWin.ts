# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/controller/task/executeQuickWin.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { Empty } from "@shared/proto/cline/common"
import { ExecuteQuickWinRequest } from "@shared/proto/cline/task"
import type { Controller } from "../index"

/**
 * Executes a quick win task with command and title
 * @param controller The controller instance
 * @param request The execute quick win request
 * @returns Empty response
 *
 * @example
 * // Usage from webview:
 * import { TaskServiceClient } from "@/services/grpc-client"
 * import { ExecuteQuickWinRequest } from "@shared/proto/cline/task"
 *
 * const request: ExecuteQuickWinRequest = {
 *   command: "npm install",
 *   title: "Install dependencies"
 * }
 *
 * TaskServiceClient.executeQuickWin(request)
 *   .then(() => console.log("Quick win executed successfully"))
 *   .catch(error => console.error("Failed to execute quick win:", error))
 */
export async function executeQuickWin(controller: Controller, request: ExecuteQuickWinRequest): Promise<Empty> {
    try {
        const { command, title } = request
        console.log(`Received executeQuickWin: command='${command}', title='${title}'`)
        await controller.initTask(title)
        return Empty.create({})
    } catch (error) {
        console.error("Failed to execute quick win:", error)
        throw error
    }
}
