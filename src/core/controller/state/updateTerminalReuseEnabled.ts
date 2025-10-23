// POKERTOOL-HEADER-START
// ---
// schema: pokerheader.v1
// project: pokertool
// file: src/core/controller/state/updateTerminalReuseEnabled.ts
// version: v28.0.0
// last_commit: '2025-09-23T08:41:38+01:00'
// fixes:
// - date: '2025-09-25'
//   summary: Enhanced enterprise documentation and comprehensive unit tests added
// ---
// POKERTOOL-HEADER-END
import * as proto from "@/shared/proto";
import { Controller } from "../index";

export async function updateTerminalReuseEnabled(
	controller: Controller,
	request: proto.cline.BooleanRequest,
): Promise<proto.cline.Empty> {
	const enabled = request.value;

	// Update the terminal reuse setting in the state
	controller.stateManager.setGlobalState("terminalReuseEnabled", enabled);

	// Broadcast state update to all webviews
	await controller.postStateToWebview();

	return proto.cline.Empty.create({});
}
