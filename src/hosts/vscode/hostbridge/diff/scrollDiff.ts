# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/hosts/vscode/hostbridge/diff/scrollDiff.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { ScrollDiffRequest, ScrollDiffResponse } from "@/shared/proto/index.host"

export async function scrollDiff(_request: ScrollDiffRequest): Promise<ScrollDiffResponse> {
    throw new Error("diffService is not supported. Use the VscodeDiffViewProvider.")
}
