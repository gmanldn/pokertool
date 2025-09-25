# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/utils/storage.ts
# version: v20.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
import getFolderSize from "get-folder-size"
import path from "path"
import { HostProvider } from "@/hosts/host-provider"

/**
 * Gets the total size of tasks and checkpoints directories
 * @returns The total size in bytes, or null if calculation fails
 */
export async function getTotalTasksSize(): Promise<number | null> {
	const tasksDir = path.resolve(HostProvider.get().globalStorageFsPath, "tasks")
	const checkpointsDir = path.resolve(HostProvider.get().globalStorageFsPath, "checkpoints")

	try {
		const tasksSize = await getFolderSize.loose(tasksDir)
		const checkpointsSize = await getFolderSize.loose(checkpointsDir)
		return tasksSize + checkpointsSize
	} catch (error) {
		console.error("Failed to calculate total task size:", error)
		return null
	}
}
