# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/hosts/vscode/hostbridge/window/getVisibleTabs.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { window } from "vscode"
import { GetVisibleTabsRequest, GetVisibleTabsResponse } from "@/shared/proto/host/window"

export async function getVisibleTabs(_: GetVisibleTabsRequest): Promise<GetVisibleTabsResponse> {
    const visibleTabPaths = window.visibleTextEditors?.map((editor) => editor.document?.uri?.fsPath).filter(Boolean)

    return GetVisibleTabsResponse.create({ paths: visibleTabPaths })
}
