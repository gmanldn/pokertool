# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: src/integrations/checkpoints/types.ts
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
/**
 * Common interface for checkpoint managers
 * Allows single-root and multi-root managers to be used interchangeably
 */
export interface ICheckpointManager {
	saveCheckpoint(isAttemptCompletionMessage?: boolean, completionMessageTs?: number): Promise<void>

	restoreCheckpoint(messageTs: number, restoreType: any, offset?: number): Promise<any>

	doesLatestTaskCompletionHaveNewChanges(): Promise<boolean>

	commit(): Promise<string | undefined>

	presentMultifileDiff?(messageTs: number, seeNewChangesSinceLastTaskCompletion: boolean): Promise<void>

	// Optional method for multi-root specific initialization
	initialize?(): Promise<void>

	// Optional method for checking and initializing checkpoint tracker
	checkpointTrackerCheckAndInit?(): Promise<any>
}
