# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/controller/task/getTotalTasksSize.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { EmptyRequest, Int64 } from "@shared/proto/cline/common"
import { getTotalTasksSize as calculateTotalTasksSize } from "../../../utils/storage"
import { Controller } from ".."

/**
 * Gets the total size of all tasks including task data and checkpoints
 * @param controller The controller instance
 * @param _request The empty request
 * @returns The total size as an Int64 value
 */
export async function getTotalTasksSize(_controller: Controller, _request: EmptyRequest): Promise<Int64> {
	const totalSize = await calculateTotalTasksSize()
	return { value: totalSize || 0 }
}
