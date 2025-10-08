# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/hosts/vscode/hostbridge/window/showOpenDialogue.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import * as vscode from "vscode"
import { SelectedResources, ShowOpenDialogueRequest } from "@/shared/proto/host/window"

export async function showOpenDialogue(request: ShowOpenDialogueRequest): Promise<SelectedResources> {
	const options: vscode.OpenDialogOptions = {}

	if (request.canSelectMany !== undefined) {
		options.canSelectMany = request.canSelectMany
	}

	if (request.openLabel !== undefined) {
		options.openLabel = request.openLabel
	}

	if (request.filters?.files) {
		options.filters = {
			Files: request.filters.files,
		}
	}

	const selectedResources = await vscode.window.showOpenDialog(options)

	// Convert back to path format
	return SelectedResources.create({
		paths: selectedResources ? selectedResources.map((uri) => uri.fsPath) : [],
	})
}
