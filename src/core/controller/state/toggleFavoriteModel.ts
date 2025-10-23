// POKERTOOL-HEADER-START
// ---
// schema: pokerheader.v1
// project: pokertool
// file: src/core/controller/state/toggleFavoriteModel.ts
// version: v28.0.0
// last_commit: '2025-09-23T08:41:38+01:00'
// fixes:
// - date: '2025-09-25'
//   summary: Enhanced enterprise documentation and comprehensive unit tests added
// ---
// POKERTOOL-HEADER-END
import { Empty, StringRequest } from "@shared/proto/cline/common";
import { telemetryService } from "@/services/telemetry";
import { Controller } from "..";

/**
 * Toggles a model's favorite status
 * @param controller The controller instance
 * @param request The request containing the model ID to toggle
 * @returns An empty response
 */
export async function toggleFavoriteModel(
	controller: Controller,
	request: StringRequest,
): Promise<Empty> {
	try {
		if (!request.value) {
			throw new Error("Model ID is required");
		}

		const modelId = request.value;

		const favoritedModelIds =
			controller.stateManager.getGlobalStateKey("favoritedModelIds");

		// Toggle favorite status
		const updatedFavorites = favoritedModelIds.includes(modelId)
			? favoritedModelIds.filter((id) => id !== modelId)
			: [...favoritedModelIds, modelId];

		controller.stateManager.setGlobalState(
			"favoritedModelIds",
			updatedFavorites,
		);

		// Capture telemetry for model favorite toggle
		const isFavorited = !favoritedModelIds.includes(modelId);
		telemetryService.captureModelFavoritesUsage(modelId, isFavorited);

		// Post state to webview without changing any other configuration
		await controller.postStateToWebview();

		return Empty.create();
	} catch (error) {
		console.error(
			`Failed to toggle favorite status for model ${request.value}:`,
			error,
		);
		throw error;
	}
}
