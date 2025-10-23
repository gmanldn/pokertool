// POKERTOOL-HEADER-START
// ---
// schema: pokerheader.v1
// project: pokertool
// file: src/shared/HistoryItem.ts
// version: v28.0.0
// last_commit: '2025-09-23T08:41:38+01:00'
// fixes:
// - date: '2025-09-25'
//   summary: Enhanced enterprise documentation and comprehensive unit tests added
// ---
// POKERTOOL-HEADER-END
export type HistoryItem = {
    id: string
    ulid?: string // ULID for better tracking and metrics
    ts: number
    task: string
    tokensIn: number
    tokensOut: number
    cacheWrites?: number
    cacheReads?: number
    totalCost: number

    size?: number
    shadowGitConfigWorkTree?: string
    cwdOnTaskInitialization?: string
    conversationHistoryDeletedRange?: [number, number]
    isFavorited?: boolean
    checkpointManagerErrorMessage?: string
}
