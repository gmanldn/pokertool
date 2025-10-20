# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/hosts/vscode/hostbridge/window/openSettings.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import * as vscode from "vscode"
import { OpenSettingsRequest, OpenSettingsResponse } from "@/shared/proto/host/window"

export async function openSettings(request: OpenSettingsRequest): Promise<OpenSettingsResponse> {
    // VS Code can be queried to focus a specific setting section
    await vscode.commands.executeCommand("workbench.action.openSettings", request.query ?? undefined)
    return OpenSettingsResponse.create({})
}
