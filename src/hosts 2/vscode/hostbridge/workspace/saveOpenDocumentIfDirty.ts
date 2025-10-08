# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/hosts/vscode/hostbridge/workspace/saveOpenDocumentIfDirty.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { arePathsEqual } from "@utils/path"
import * as vscode from "vscode"
import { SaveOpenDocumentIfDirtyRequest, SaveOpenDocumentIfDirtyResponse } from "@/shared/proto/index.host"

export async function saveOpenDocumentIfDirty(request: SaveOpenDocumentIfDirtyRequest): Promise<SaveOpenDocumentIfDirtyResponse> {
	const existingDocument = vscode.workspace.textDocuments.find((doc) => arePathsEqual(doc.uri.fsPath, request.filePath))
	if (existingDocument && existingDocument.isDirty) {
		await existingDocument.save()
		return { wasSaved: true }
	}
	return {}
}
