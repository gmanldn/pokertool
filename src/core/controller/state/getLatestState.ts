# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/controller/state/getLatestState.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { EmptyRequest } from "@shared/proto/cline/common"
import { State } from "@shared/proto/cline/state"
import { Controller } from "../index"

/**
 * Get the latest extension state
 * @param controller The controller instance
 * @param request The empty request
 * @returns The current extension state
 */
export async function getLatestState(controller: Controller, _: EmptyRequest): Promise<State> {
	// Get the state using the existing method
	const state = await controller.getStateToPostToWebview()

	// Convert the state to a JSON string
	const stateJson = JSON.stringify(state)

	// Return the state as a JSON string
	return State.create({
		stateJson,
	})
}
