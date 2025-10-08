# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/core/context/context-tracking/ModelContextTracker.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import { getTaskMetadata, saveTaskMetadata } from "@core/storage/disk"
import * as vscode from "vscode"

export class ModelContextTracker {
	readonly taskId: string
	private context: vscode.ExtensionContext

	constructor(context: vscode.ExtensionContext, taskId: string) {
		this.context = context
		this.taskId = taskId
	}

	async recordModelUsage(apiProviderId: string, modelId: string, mode: string) {
		const metadata = await getTaskMetadata(this.context, this.taskId)

		if (!metadata.model_usage) {
			metadata.model_usage = []
		}

		// check to see if the last entry is the same as the new one
		const lastEntry = metadata.model_usage[metadata.model_usage.length - 1]
		if (
			lastEntry &&
			lastEntry.model_id === modelId &&
			lastEntry.model_provider_id === apiProviderId &&
			lastEntry.mode === mode
		) {
			return
		}

		metadata.model_usage.push({
			ts: Date.now(),
			model_id: modelId,
			model_provider_id: apiProviderId,
			mode: mode,
		})

		await saveTaskMetadata(this.context, this.taskId, metadata)
	}
}
