// POKERTOOL-HEADER-START
// ---
// schema: pokerheader.v1
// project: pokertool
// file: src/core/controller/file/toggleWorkflow.ts
// version: v28.0.0
// last_commit: '2025-09-23T08:41:38+01:00'
// fixes:
// - date: '2025-09-25'
//   summary: Enhanced enterprise documentation and comprehensive unit tests added
// ---
// POKERTOOL-HEADER-END
import { ClineRulesToggles, ToggleWorkflowRequest } from "@shared/proto/cline/file"
import { Controller } from ".."

/**
 * Toggles a workflow on or off
 * @param controller The controller instance
 * @param request The request containing the workflow path and enabled state
 * @returns The updated workflow toggles
 */
export async function toggleWorkflow(controller: Controller, request: ToggleWorkflowRequest): Promise<ClineRulesToggles> {
	const { workflowPath, enabled, isGlobal } = request

	if (!workflowPath || typeof enabled !== "boolean") {
		console.error("toggleWorkflow: Missing or invalid parameters", {
			workflowPath,
			enabled: typeof enabled === "boolean" ? enabled : `Invalid: ${typeof enabled}`,
		})
		throw new Error("Missing or invalid parameters for toggleWorkflow")
	}

	// Update the toggles based on isGlobal flag
	if (isGlobal) {
		// Global workflows
		const toggles = controller.stateManager.getGlobalSettingsKey("globalWorkflowToggles")
		toggles[workflowPath] = enabled
		controller.stateManager.setGlobalState("globalWorkflowToggles", toggles)
		await controller.postStateToWebview()

		// Return the global toggles
		return ClineRulesToggles.create({ toggles: toggles })
	} else {
		// Workspace workflows
		const toggles = controller.stateManager.getWorkspaceStateKey("workflowToggles")
		toggles[workflowPath] = enabled
		controller.stateManager.setWorkspaceState("workflowToggles", toggles)
		await controller.postStateToWebview()

		// Return the workspace toggles
		return ClineRulesToggles.create({ toggles: toggles })
	}
}
