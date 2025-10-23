// POKERTOOL-HEADER-START
// ---
// schema: pokerheader.v1
// project: pokertool
// file: src/core/api/transform/stream.ts
// version: v28.0.0
// last_commit: '2025-09-23T08:41:38+01:00'
// fixes:
// - date: '2025-09-25'
//   summary: Enhanced enterprise documentation and comprehensive unit tests added
// ---
// POKERTOOL-HEADER-END
export type ApiStream = AsyncGenerator<ApiStreamChunk>
export type ApiStreamChunk = ApiStreamTextChunk | ApiStreamReasoningChunk | ApiStreamUsageChunk

export interface ApiStreamTextChunk {
    type: "text"
    text: string
}

export interface ApiStreamReasoningChunk {
    type: "reasoning"
    reasoning: string
}

export interface ApiStreamUsageChunk {
    type: "usage"
    inputTokens: number
    outputTokens: number
    cacheWriteTokens?: number
    cacheReadTokens?: number
    thoughtsTokenCount?: number // openrouter
    totalCost?: number // openrouter
}
