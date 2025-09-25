# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/controller/state/updateTerminalConnectionTimeout.ts
# version: v20.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { UpdateTerminalConnectionTimeoutRequest, UpdateTerminalConnectionTimeoutResponse } from "@shared/proto/cline/state"
import { Controller } from "../index"

export async function updateTerminalConnectionTimeout(
	controller: Controller,
	request: UpdateTerminalConnectionTimeoutRequest,
): Promise<UpdateTerminalConnectionTimeoutResponse> {
	const timeoutMs = request.timeoutMs

	// Update the terminal connection timeout setting in the state
	controller.stateManager.setGlobalState("shellIntegrationTimeout", timeoutMs || 4000)

	// Broadcast state update to all webviews
	await controller.postStateToWebview()

	return { timeoutMs }
}
