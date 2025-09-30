# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/hosts/vscode/hostbridge/diff/openMultiFileDiff.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import path from "path"
import * as vscode from "vscode"
import { OpenMultiFileDiffRequest, OpenMultiFileDiffResponse } from "@/shared/proto/index.host"
import { getCwd } from "@/utils/path"
import { DIFF_VIEW_URI_SCHEME } from "../../VscodeDiffViewProvider"

export async function openMultiFileDiff(request: OpenMultiFileDiffRequest): Promise<OpenMultiFileDiffResponse> {
	const cwd = await getCwd()
	await vscode.commands.executeCommand(
		"vscode.changes",
		request.title,
		request.diffs.map((diff) => {
			const file = vscode.Uri.file(diff.filePath || "")
			const relativePath = path.relative(cwd, diff.filePath || "")
			const left = diff.leftContent ?? ""
			const right = diff.rightContent ?? ""
			return [
				file,
				vscode.Uri.parse(`${DIFF_VIEW_URI_SCHEME}:${relativePath}`).with({
					query: Buffer.from(left).toString("base64"),
				}),
				vscode.Uri.parse(`${DIFF_VIEW_URI_SCHEME}:${relativePath}`).with({
					query: Buffer.from(right).toString("base64"),
				}),
			]
		}),
	)

	return {}
}
