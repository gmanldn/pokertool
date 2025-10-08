# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/hosts/vscode/hostbridge/window/openFile.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import * as vscode from "vscode"
import { OpenFileRequest, OpenFileResponse } from "@/shared/proto/host/window"

export async function openFile(request: OpenFileRequest): Promise<OpenFileResponse> {
    await vscode.commands.executeCommand("vscode.open", vscode.Uri.file(request.filePath))
    return OpenFileResponse.create({})
}
