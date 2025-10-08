# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/hosts/vscode/hostbridge/diff/replaceText.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { ReplaceTextRequest, ReplaceTextResponse } from "@/shared/proto/index.host"

export async function replaceText(_request: ReplaceTextRequest): Promise<ReplaceTextResponse> {
	throw new Error("diffService is not supported. Use the VscodeDiffViewProvider.")
}
