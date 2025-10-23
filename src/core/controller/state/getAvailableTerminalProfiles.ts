// POKERTOOL-HEADER-START
// ---
// schema: pokerheader.v1
// project: pokertool
// file: src/core/controller/state/getAvailableTerminalProfiles.ts
// version: v28.0.0
// last_commit: '2025-09-23T08:41:38+01:00'
// fixes:
// - date: '2025-09-25'
//   summary: Enhanced enterprise documentation and comprehensive unit tests added
// ---
// POKERTOOL-HEADER-END
import * as proto from "@/shared/proto";
import { getAvailableTerminalProfiles as getTerminalProfilesFromShell } from "../../../utils/shell";
import { Controller } from "../index";

export async function getAvailableTerminalProfiles(
	_controller: Controller,
	_request: proto.cline.EmptyRequest,
): Promise<proto.cline.TerminalProfiles> {
	const profiles = getTerminalProfilesFromShell();

	return proto.cline.TerminalProfiles.create({
		profiles: profiles.map((profile) => ({
			id: profile.id,
			name: profile.name,
			path: profile.path || "",
			description: profile.description || "",
		})),
	});
}
