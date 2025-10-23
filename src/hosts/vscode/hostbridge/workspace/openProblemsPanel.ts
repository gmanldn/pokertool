// POKERTOOL-HEADER-START
// ---
// schema: pokerheader.v1
// project: pokertool
// file: src/hosts/vscode/hostbridge/workspace/openProblemsPanel.ts
// version: v28.0.0
// last_commit: '2025-09-23T08:41:38+01:00'
// fixes:
// - date: '2025-09-25'
//   summary: Enhanced enterprise documentation and comprehensive unit tests added
// ---
// POKERTOOL-HEADER-END
import * as vscode from "vscode"
import { OpenProblemsPanelRequest, OpenProblemsPanelResponse } from "@/shared/proto/index.host"

export async function openProblemsPanel(_: OpenProblemsPanelRequest): Promise<OpenProblemsPanelResponse> {
	vscode.commands.executeCommand("workbench.actions.view.problems")
	return {}
}
