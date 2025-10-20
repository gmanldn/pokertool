# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/hosts/vscode/hostbridge/window/getOpenTabs.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { TabInputText, window } from "vscode"
import { GetOpenTabsRequest, GetOpenTabsResponse } from "@/shared/proto/host/window"

export async function getOpenTabs(_: GetOpenTabsRequest): Promise<GetOpenTabsResponse> {
    const openTabPaths = window.tabGroups.all
        .flatMap((group) => group.tabs)
        .map((tab) => (tab.input as TabInputText)?.uri?.fsPath)
        .filter(Boolean)

    return GetOpenTabsResponse.create({ paths: openTabPaths })
}
