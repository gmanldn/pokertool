# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/controller/file/toggleCursorRule.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import type { ToggleCursorRuleRequest } from "@shared/proto/cline/file"
import { ClineRulesToggles } from "@shared/proto/cline/file"
import type { Controller } from "../index"

/**
 * Toggles a Cursor rule (enable or disable)
 * @param controller The controller instance
 * @param request The toggle request
 * @returns The updated Cursor rule toggles
 */
export async function toggleCursorRule(controller: Controller, request: ToggleCursorRuleRequest): Promise<ClineRulesToggles> {
    const { rulePath, enabled } = request

    if (!rulePath || typeof enabled !== "boolean") {
        console.error("toggleCursorRule: Missing or invalid parameters", {
            rulePath,
            enabled: typeof enabled === "boolean" ? enabled : `Invalid: ${typeof enabled}`,
        })
        throw new Error("Missing or invalid parameters for toggleCursorRule")
    }

    // Update the toggles in workspace state
    const toggles = controller.stateManager.getWorkspaceStateKey("localCursorRulesToggles")
    toggles[rulePath] = enabled
    controller.stateManager.setWorkspaceState("localCursorRulesToggles", toggles)

    // Get the current state to return in the response
    const cursorToggles = controller.stateManager.getWorkspaceStateKey("localCursorRulesToggles")

    return ClineRulesToggles.create({
        toggles: cursorToggles,
    })
}
